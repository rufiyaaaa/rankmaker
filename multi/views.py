import logging
import datetime
from django import forms

from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views import generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .rating_functions import put_badge, separate, separate_1on1, refresh_rating
from .models import Affiliation, Player, Game, Duel, Rating, Team, Participant, Notice
from .forms import GameCreate1on1Form, GameCreateForm, PlayerCreateForm, TeamCreateForm, TeamConfigForm, BatchPlayerCreateForm
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, generic.TemplateView):
    template_name = "multi/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user
        context['notice'] = Notice.objects.filter(release_date__lte=datetime.datetime.now()).order_by('-release_date')[0:5]

        if Affiliation.objects.filter(user=self.request.user).count() != 0:
            affl = Affiliation.objects.get(user=self.request.user)
            players = Player.objects.filter(team=affl.team).filter(inactive=False).order_by('-ltst_rating')[0:3]
            context['ranking'] = players
            context['team'] = affl.team
        else:
            context['ranking'] = Player.objects.none()

        return context


class RankingView(LoginRequiredMixin, generic.TemplateView):
    template_name = "multi/ranking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user

        if Affiliation.objects.filter(user=self.request.user).count() != 0:
            affl = Affiliation.objects.get(user=self.request.user)
            players = Player.objects.filter(team=affl.team).filter(inactive=False).order_by('-ltst_rating')
            context['ranking'] = players
            context['team'] = affl.team
        else:
            context['ranking'] = Player.objects.none()

        return context


class RankingExtView(generic.TemplateView):
    template_name = "multi/ranking_ext.html"

    def get_context_data(self, **kwargs):
        page_id = self.kwargs.get('page_id')
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(page_id=page_id)

        players = Player.objects.filter(team=context['team']).filter(inactive=False).order_by('-ltst_rating')
        context['ranking'] = players

        return context


class GameListView(LoginRequiredMixin, generic.ListView):
    model = Game
    template_name = 'multi/game_list.html'
    paginate_by = 5

    def get_queryset(self):
        affl = Affiliation.objects.get(user=self.request.user)
        game_list = Game.objects.filter(team=affl.team).order_by('-date')
        return game_list

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class GameDetailView(LoginRequiredMixin, generic.DetailView):
    model = Game
    template_name = 'multi/game_detail.html'

    def get_context_data(self, **kwargs):
        """Gameに関連するParticipantレコードを渡す"""
        context = super().get_context_data(**kwargs)
        context['participants'] = Participant.objects.filter(game=context['game']).order_by('rank')

        return context


class GameCreateView(LoginRequiredMixin, generic.CreateView):  # 本丸
    model = Game
    template_name = 'multi/game_create.html'
    form_class = GameCreateForm

    def get_initial(self):
        affl = Affiliation.objects.get(user=self.request.user)
        initial = super(GameCreateView, self).get_initial()
        initial['players'] = Player.objects.filter(team=affl.team).filter(inactive=False).order_by('pk')
        initial['initial_value'] = Participant.objects.none()
        return initial

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.date = make_aware(game.date)
        game.save()

        # 参加者とその順位から、Duel、Participantを作成
        separate(form.data, game)

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game)

        # 更新が必要なGameにバッヂ付けをする
        put_badge(game)

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行

        messages.error(self.request, "対戦結果の登録に失敗しました。")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('multi:game_list')


class GameCreate1on1View(LoginRequiredMixin, generic.CreateView):  # 本丸
    model = Game
    template_name = 'multi/game_create_1on1.html'
    form_class = GameCreate1on1Form

    def get_initial(self):
        user = self.request.user
        affl = Affiliation.objects.get(user=user)
        initial = super().get_initial()
        initial['players'] = Player.objects.filter(team=affl.team).order_by('id')
        initial['winner'] = initial['players'].first
        initial['loser'] = initial['players'].first
        initial['even'] = "off"
        return initial

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.date = make_aware(game.date)
        game.save()

        # 参加者とその順位から、Duel、Participantを作成
        separate_1on1(form.data, game)

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game)

        # 更新が必要なGameにバッヂ付けをする

        put_badge(game)

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行

        messages.error(self.request, "対戦結果の登録に失敗しました。")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('multi:game_list')


class GameUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Game
    template_name = 'multi/game_update.html'
    form_class = GameCreateForm

    def get_initial(self):
        affl = Affiliation.objects.get(user=self.request.user)
        initial = super(GameUpdateView, self).get_initial()
        initial['players'] = Player.objects.filter(team=affl.team)
        game = self.object
        initial['initial_value'] = game.participant_game.all()
        return initial

    def get_success_url(self):
        return reverse_lazy('multi:game_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.date = make_aware(game.date)
        game.save()

        # Duel, Participantを一旦全削除
        game.duel_game.all().delete()
        game.participant_game.all().delete()

        # 参加者とその順位から、Duel、Participationを作成
        separate(form.data, game)

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game)

        # 更新が必要なGameにバッヂ付けをする

        put_badge(game)

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "対戦結果の更新に失敗しました。")
        return super().form_invalid(form)


class GameUpdate1on1View(LoginRequiredMixin, generic.UpdateView):
    model = Game
    template_name = 'multi/game_update_1on1.html'
    form_class = GameCreate1on1Form

    def get_initial(self):
        game = self.object
        initial = super().get_initial()
        initial['players'] = Player.objects.filter(team=game.team).order_by('id')
        initial['winner'] = Duel.objects.get(game=game).winner.id
        initial['loser'] = Duel.objects.get(game=game).loser.id
        initial['even'] = Duel.objects.get(game=game).even
        return initial

    def get_success_url(self):
        return reverse_lazy('multi:game_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.date = make_aware(game.date)
        game.save()

        # Duel, Participantを一旦全削除
        game.duel_game.all().delete()
        game.participant_game.all().delete()

        # 参加者とその順位から、Duel、Participationを作成
        separate_1on1(form.data, game)

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game)

        # 更新が必要なGameにバッヂ付けをする
        put_badge(game)

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "対戦結果の更新に失敗しました。")
        return super().form_invalid(form)


class GameDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Game
    template_name = 'multi/game_delete.html'
    success_url = reverse_lazy('multi:game_list')

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']  # 後でゲーム情報が必要になるので、削除前に取り出しておく
        game = Game.objects.get(pk=pk)
        put_badge(game)
        messages.success(self.request, "対戦結果を削除しました。")
        delete = super().delete(request, *args, **kwargs)
        return delete


class PlayerListView(LoginRequiredMixin, generic.ListView):
    model = Player
    template_name = 'multi/player_list.html'
    paginate_by = 15

    def get_queryset(self):
        affl = Affiliation.objects.get(user=self.request.user)
        players = Player.objects.filter(team=affl.team).order_by('pk')
        return players

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class PlayerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Player
    template_name = 'multi/player_detail.html'

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        context['participant_set'] = Participant.objects.filter(player=self.object).order_by('game__date')
        return context


class BatchPlayerCreateView(LoginRequiredMixin, generic.FormView):
    template_name = 'multi/batch_player_create.html'
    form_class = BatchPlayerCreateForm
    success_url = reverse_lazy('multi:player_list')

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        affl = Affiliation.objects.get(user=self.request.user)
        names = form.cleaned_data['name'].splitlines()
        for name in names:
            player = Player()
            player.team = affl.team
            player.name = name
            player.save()
        msg = "メンバーを" + str(len(names)) + "件追加しました。"
        messages.success(self.request, msg)
        return super().form_valid(form)


class PlayerCreateView(LoginRequiredMixin, generic.CreateView):
    model = Player
    template_name = 'multi/player_create.html'
    form_class = PlayerCreateForm
    success_url = reverse_lazy('multi:player_list')

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        player = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        player.team = affl.team
        player.save()
        messages.success(self.request, "メンバーを追加しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行
        messages.error(self.request, "メンバーの追加に失敗しました。")
        return super().form_invalid(form)


class PlayerUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Player
    template_name = 'multi/player_update.html'
    form_class = PlayerCreateForm

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def get_success_url(self):
        return reverse_lazy('multi:player_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        messages.success(self.request, 'メンバーを更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "メンバーの更新に失敗しました。")
        return super().form_invalid(form)


class PlayerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Player
    template_name = 'multi/player_delete.html'
    success_url = reverse_lazy('multi:player_list')

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "メンバーを削除しました。")
        return super().delete(request, *args, **kwargs)


class TeamCreateView(LoginRequiredMixin, generic.CreateView):
    model = Team
    template_name = 'multi/team_create.html'
    form_class = TeamCreateForm
    success_url = reverse_lazy('multi:player_list')

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        team = form.save(commit=False)
        team.save()
        affl = Affiliation()
        affl.team = team
        affl.user = self.request.user
        affl.save()
        self.request.user.have_multi_team = True
        self.request.user.save()

        messages.success(self.request, "チームを作成しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行
        messages.error(self.request, "チームの作成に失敗しました。")
        return super().form_invalid(form)


class TeamDetailView(LoginRequiredMixin, generic.DetailView):
    model = Team
    template_name = 'multi/team_detail.html'

    def get_object(self, queryset=None):
        return Affiliation.objects.get(user=self.request.user).team

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class TeamConfigView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    template_name = 'multi/team_config.html'
    form_class = TeamConfigForm
    success_url = reverse_lazy('multi:team_detail')

    def get_object(self, queryset=None):
        return Affiliation.objects.get(user=self.request.user).team

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['affl'] = affl
        context['team'] = affl.team
        return context

    def form_valid(self, form):
        messages.success(self.request, 'チーム設定を更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "チーム設定の更新に失敗しました。")
        return super().form_invalid(form)


class TeamDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Affiliation
    template_name = 'multi/team_delete.html'
    success_url = reverse_lazy('multi:home')

    # def get_context_data(self, **kwargs):
    #     affl = Affiliation.objects.get(user=self.request.user)
    #     context = super().get_context_data(**kwargs)
    #     context['affl'] = affl
    #     return context

    def delete(self, request, *args, **kwargs):
        self.request.user.have_multi_team = False
        self.request.user.save()
        messages.success(self.request, "チームを削除しました。")
        return super().delete(request, *args, **kwargs)


class NoticeDetailView(LoginRequiredMixin, generic.DetailView):
    model = Notice
    template_name = 'multi/notice_detail.html'


class NoticeListView(LoginRequiredMixin, generic.ListView):
    model = Notice
    template_name = 'multi/notice_list.html'
    paginate_by = 5

    def get_queryset(self):
        return Notice.objects.all().order_by('-release_date')
