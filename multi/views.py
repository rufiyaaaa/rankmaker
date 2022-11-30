import logging
import datetime
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from rankmaker.settings_common import TIME_ZONE
from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views import generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .rating_functions import put_badge, separate, separate_1on1, refresh_rating
from .models import Affiliation, Player, Game, Duel, Rating, Team, Participant, Notice
from .forms import GameCreate1on1Form, GameCreateForm, PlayerCreateForm, TeamCreateForm, TeamConfigForm,\
    BatchPlayerCreateForm, BatchGameCreateForm, TeamChoiceForm
from django.core.exceptions import ValidationError
from . import graph
from dateutil.parser import parser

logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, generic.TemplateView):
    template_name = "multi/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user
        context['notice'] = Notice.objects.filter(release_date__lte=datetime.datetime.now(datetime.timezone.utc)).order_by('-release_date')[0:5]

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
    paginate_by = 10

    def get_queryset(self):
        affl = Affiliation.objects.get(user=self.request.user)
        game_list = Game.objects.filter(team=affl.team).order_by('-date')
        return game_list

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class GameDetailView(generic.DetailView):
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
        initial['even'] = None
        return initial

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.date = make_aware(game.date)
        game.save()

        # 参加者とその順位から、Duel、Participantを作成。参加者と順位は辞書型で、pkと順位の数字
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


class BatchGameCreateView(LoginRequiredMixin, generic.FormView):
    template_name = 'multi/batch_game_create.html'
    form_class = BatchGameCreateForm
    success_url = reverse_lazy('multi:game_list')

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        affl = Affiliation.objects.get(user=self.request.user)
        lines = form.cleaned_data['text'].splitlines()
        lines.append('')
        line_count = 0
        player_temp = ()
        rank_data = {}
        game = Game()
        for line in lines:
            if line == "":
                game.team = affl.team
                game.save()         # ここで各種データがきちんと入っているかを確認したい

                # 参加者とその順位から、Duel、Participantを作成
                separate(rank_data, game)
                # レーティングの更新処理をする。キーとなる引数は、Game.date
                refresh_rating(game)
                # 更新が必要なGameにバッヂ付けをする
                put_badge(game)

                line_count = 0
                rank_data = {}
                game = Game()
            else:
                if line_count == 0:
                    game.name = line
                elif line_count == 1:
                    game.date = parser().parse(line)    # データの形が合っているかどうかはひとまず無視
                else:
                    player_temp = line.split(',')
                    player_id = Player.objects.filter(team=affl.team).get(name=player_temp[0]).id
                    rank_data[str(player_id)] = player_temp[1]

                line_count = line_count + 1

        msg = str(len(lines)) + "名のメンバーを追加しました。"
        messages.success(self.request, msg)
        return super().form_valid(form)


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
        return super().delete(request, *args, **kwargs)


class SUGameListView(LoginRequiredMixin, generic.ListView):
    model = Game
    template_name = 'multi/game_list.html'

    def get_queryset(self):
        game_list = Game.objects.all().order_by('-date')
        return game_list

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


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


class PlayerDetailView(generic.DetailView):
    model = Player
    template_name = 'multi/player_detail.html'

    def get_context_data(self, **kwargs):
        # affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        # context['team'] = affl.team
        participant_set = Participant.objects.filter(player=self.object).order_by('game__date')[:15]
        context['participant_set'] = participant_set

        # グラフオブジェクト
        x = [x.game.date.astimezone(datetime.timezone(datetime.timedelta(hours=9))) for x in participant_set]           # X軸データ
        y = [y.new_appr for y in participant_set]        # Y軸データ
        chart = graph.plot_graph(x, y)          # グラフ作成

        # 変数を渡す
        context['chart'] = chart
        return context

    # get処理
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
        msg = str(len(names)) + "名のメンバーを追加しました。"
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
        team.owner = self.request.user
        team.save()
        affl = Affiliation.objects.filter(user=self.request.user)
        if not affl:
            affl = Affiliation()
            affl.user = self.request.user
        else:
            affl = Affiliation.objects.get(user=self.request.user)
        affl.team = team
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

    def get_initial(self):
        user = self.request.user
        affl = Affiliation.objects.get(user=user)
        initial = super().get_initial()
        initial['affl'] = affl

        return initial

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context.update({
            'affl': affl,
            'team': affl.team
        })
        return context

    def form_valid(self, form):
        # offset_termに変更があった場合自チームのGame全てに対してneed_to_recalc=Trueを設定する
        old_data = self.object.tracker.saved_data['offset_term']
        if old_data != self.object.offset_term:
            games = Game.objects.filter(team=self.object)
            games.update(need_to_recalc=True)
            messages.success(self.request, 'チーム設定を更新しました。レーティングの再計算をしてください')
        else:
            messages.success(self.request, 'チーム設定を更新しました。')

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "チーム設定の更新に失敗しました。")
        return super().form_invalid(form)


class TeamDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Team
    template_name = 'multi/team_delete.html'
    success_url = reverse_lazy('multi:home')

    # def get_context_data(self, **kwargs):
    #     affl = Affiliation.objects.get(user=self.request.user)
    #     context = super().get_context_data(**kwargs)
    #     context['affl'] = affl
    #     return context

    def delete(self, request, *args, **kwargs):
        team_num = Team.objects.filter(owner=self.request.user).count()
        if team_num == 1:
            self.request.user.have_multi_team = False
            self.request.user.save()

        messages.success(self.request, "チームを削除しました。")
        super().delete(request, *args, **kwargs)
        # afflのteamを適当なTeamにする
        affl = Affiliation.objects.get(user=self.request.user)
        affl.team = Team.objects.filter(owner=self.request.user).first()
        affl.save()
        return HttpResponseRedirect(self.success_url)


class TeamChoiceView(LoginRequiredMixin, generic.UpdateView):
    model = Affiliation
    template_name = 'multi/team_choice.html'
    form_class = TeamChoiceForm

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def get_success_url(self):
        return reverse_lazy('multi:team_config')

    def form_valid(self, form):
        messages.success(self.request, 'チームを変更しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "チームの変更に失敗しました。")
        return super().form_invalid(form)


class NoticeDetailView(LoginRequiredMixin, generic.DetailView):
    model = Notice
    template_name = 'multi/notice_detail.html'


class NoticeListView(LoginRequiredMixin, generic.ListView):
    model = Notice
    template_name = 'multi/notice_list.html'
    paginate_by = 5

    def get_queryset(self):
        return Notice.objects.all().order_by('-release_date')


def recalc(request, pk):
    """再計算"""
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        # 再計算処理

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game)

        # 更新が必要なGameにバッヂ付けをする

        put_badge(game)

        messages.success(request, "再計算しました。")
    return redirect(request.META["HTTP_REFERER"])
