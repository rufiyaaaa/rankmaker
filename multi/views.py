import logging
import datetime
import itertools
from django import forms
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .rating_functions import refresh_rating, duel_registration, participant_registration
from .models import Affiliation, Player, Game, Duel, Rating, Team, Participant
from .forms import GameCreateForm, PlayerCreateForm, TeamCreateForm, TeamConfigForm
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, generic.TemplateView):
    template_name = "multi/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user

        if Affiliation.objects.filter(user=self.request.user).count() != 0:
            affl = Affiliation.objects.get(user=self.request.user)
            players = Player.objects.filter(team=affl.team)
            context['ranking'] = players
            context['team'] = affl.team
        else:
            context['ranking'] = Player.objects.none()

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

"""
def dynamic(request):
    content = {}
    context = {}
    form_item = {}

    qs = []
    affl = Affiliation.objects.get(user=request.user)
    players = Player.objects.filter(team=affl.team)
    for player in players:
        qs.append({'pk': player.pk, 'name': player.name})

    form_item.update({'name': forms.CharField(label='タイトル', max_length=50, required=False, initial="name")})
    form_item.update({'date': forms.DateTimeField(label='試合日時(YYYY-MM-DD HH:MM)', required=True,
                                                  initial=datetime.datetime.now())})
    for q in qs:
        form_item.update({format(q['pk']): forms.IntegerField(label=q['name'] + 'さんの順位', required=False)})

    dynamicgameform = type('DynamicGameForm', (GCTestForm,), form_item)

    entry = []
    if request.method == 'POST':

        else:
            raise ValidationError('対戦者数は2人以上にしてください')

    dynamicform = dynamicgameform(content)
    context['game_form'] = dynamicform
    return render(request, "multi/game_create.html", context)
"""


class GameCreateView(LoginRequiredMixin, generic.CreateView):  # 本丸
    model = Game
    template_name = 'multi/game_create.html'
    form_class = GameCreateForm

    def get_initial(self):
        affl = Affiliation.objects.get(user=self.request.user)
        initial = super(GameCreateView, self).get_initial()
        initial['q_set'] = Player.objects.filter(team=affl.team)
        return initial

    # def get_form_kwargs(self, *args, **kwargs):
    #     kwgs = super(GameCreateView, self).get_form_kwargs(*args, **kwargs)
    #     affl = Affiliation.objects.get(user=self.request.user)
    #     kwgs["team"] = affl.team
    #     return kwgs

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        # formの情報から、gameを作成し情報を登録
        game = form.save(commit=False)
        affl = Affiliation.objects.get(user=self.request.user)
        game.team = affl.team
        game.save()

        # 参加者とその順位から、Duel、Participationを作成
        rank_data = []
        for key in form.data:
            if key != 'csrfmiddlewaretoken' and key != 'date' and key != 'name':
                if form.data[key] != '':
                    rank_data.append([key, form.data[key]])
        rank_data.sort(key=lambda x: x[1])
        for result in rank_data:
            participant_registration(result, game)
            # 仮のRatingレコードも↑で作成(duelを作った時にそれに対して作成するのがスマート）
        for player_pair in itertools.combinations(rank_data, 2):
            duel_registration(player_pair, game)

        # レーティングの更新処理をする。キーとなる引数は、Game.date
        refresh_rating(game.date, game.team)

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行

        messages.error(self.request, "対戦結果の登録に失敗しました。")
        for ele in form:
            print(ele)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('multi:game_list')


# def create_game(request):
#     form = GameCreateForm(request.POST or None)
#     context = {'form': form}
#     if request.method == 'POST' and form.is_valid():
#         game = form
#         formset = ParticipantFormset(request.POST)
#         if formset.is_valid() and formset_check(formset):  # 本当はis_validに機能を追加したい
#             resolve_game(formset)
#             return redirect('multi:home')
#
#         # エラーメッセージ付きのformsetをテンプレートに渡せるらしい
#         else:
#             context['formset'] = formset
#
#     # GETの場合
#     else:
#         # 空のformsetをテンプレートに渡す
#         context['formset'] = ParticipantFormset()
#
#     return render(request, 'multi/game_create.html', context)


class GameUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Game
    template_name = 'multi/game_update.html'
    form_class = GameCreateForm

    def get_form_kwargs(self, *args, **kwargs):
        kwgs = super(GameUpdateView, self).get_form_kwargs(*args, **kwargs)
        affl = Affiliation.objects.get(user=self.request.user)
        kwgs["team"] = affl.team

        return kwgs

    def get_success_url(self):
        return reverse_lazy('multi:duel_update', kwargs={'game_pk': self.kwargs['pk']})

    def form_valid(self, form):
        game = form.save(commit=False)
        game.save()

        messages.success(self.request, '対戦結果を更新しました。')
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
        messages.success(self.request, "対戦結果を削除しました。")
        return super().delete(request, *args, **kwargs)


class PlayerListView(LoginRequiredMixin, generic.ListView):
    model = Player
    template_name = 'multi/player_list.html'
    paginate_by = 30

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
        return context


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


class TeamConfigView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    template_name = 'multi/team_config.html'
    form_class = TeamConfigForm
    success_url = reverse_lazy('multi:home')

    def get_object(self, queryset=None):
        return Affiliation.objects.get(user=self.request.user).team

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def form_valid(self, form):
        messages.success(self.request, 'チーム設定を更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "チーム設定の更新に失敗しました。")
        return super().form_invalid(form)





