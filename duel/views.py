import logging
from django.urls import reverse_lazy
from django.views import generic
from .forms import InquiryForm, MatchCreateForm, PlayerCreateForm, TeamCreateForm, TeamConfigForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .rating_functions import refresh_ratings
from .models import Match, Team, Rating, Player, Affiliation
from accounts.models import CustomUser

# Create your views here.
logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = "index.html"


class HomeView(LoginRequiredMixin, generic.TemplateView):
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user
        affl = Affiliation.objects.get(user=self.request.user)
        context['team'] = affl.team

        if Affiliation.objects.filter(user=self.request.user).count() != 0:
            affl = Affiliation.objects.get(user=self.request.user)
            refresh_ratings(affl.team)
            players = Player.objects.filter(team=affl.team).order_by('-latest_rating')
            context['ranking'] = players
        else:
            context['ranking'] = Player.objects.none()

        return context


class InquiryView(generic.FormView):
    template_name = "inquiry.html"
    form_class = InquiryForm
    success_url = reverse_lazy('duel:inquiry')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Inquiry sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)


class MatchListView(LoginRequiredMixin, generic.ListView):
    model = Match
    template_name = 'match_list.html'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def get_queryset(self):
        affl = Affiliation.objects.get(user=self.request.user)
        refresh_ratings(affl.team)
        matches = Match.objects.filter(team=affl.team).order_by('-date')
        return matches

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        refresh_ratings(affl.team)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class MatchDetailView(LoginRequiredMixin, generic.DetailView):
    model = Match
    template_name = 'match_detail.html'

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class MatchCreateView(LoginRequiredMixin, generic.CreateView):
    model = Match
    template_name = 'match_create.html'
    form_class = MatchCreateForm
    success_url = reverse_lazy('duel:match_list')

    def get_form_kwargs(self, *args, **kwargs):
        kwgs = super(MatchCreateView, self).get_form_kwargs(*args, **kwargs)
        affl = Affiliation.objects.get(user=self.request.user)
        kwgs["team"] = affl.team
        return kwgs

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        match = form.save(commit=False)  # userの入力が必須だが、ユーザーにそれを入力させるのは自明なのでおかしい。テクニック。
        affl = Affiliation.objects.get(user=self.request.user)
        match.team = affl.team
        match.save()
        # 勝者のレーティングを計算せず登録
        winrate = Rating()
        winrate.match = match
        winrate.player = match.winner
        winrate.save()
        # 敗者のレーティングを計算せず登録
        losrate = Rating()
        losrate.match = match
        losrate.player = match.loser
        losrate.save()
        # 仮レーティングは表示時に再計算して評価される

        messages.success(self.request, "対戦結果を登録しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行
        messages.error(self.request, "対戦結果の登録に失敗しました。")
        return super().form_invalid(form)


class MatchUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Match
    template_name = 'match_update.html'
    form_class = MatchCreateForm

    def get_form_kwargs(self, *args, **kwargs):
        kwgs = super(MatchUpdateView, self).get_form_kwargs(*args, **kwargs)
        affl = Affiliation.objects.get(user=self.request.user)
        kwgs["team"] = affl.team

        return kwgs

    def get_success_url(self):
        return reverse_lazy('duel:match_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        match = form.save(commit=False)
        match.save()

        messages.success(self.request, '対戦結果を更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "対戦結果の更新に失敗しました。")
        return super().form_invalid(form)


class MatchDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Match
    template_name = 'match_delete.html'
    success_url = reverse_lazy('duel:match_list')

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
    template_name = 'player_list.html'
    paginate_by = 30

    def get_queryset(self):
        affl = Affiliation.objects.get(user=self.request.user)
        refresh_ratings(affl.team)
        players = Player.objects.filter(team=affl.team).order_by('pk')
        return players

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        refresh_ratings(affl.team)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class PlayerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Player
    template_name = 'player_detail.html'

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context


class PlayerCreateView(LoginRequiredMixin, generic.CreateView):
    model = Player
    template_name = 'player_create.html'
    form_class = PlayerCreateForm
    success_url = reverse_lazy('duel:player_list')

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
    template_name = 'player_update.html'
    form_class = PlayerCreateForm

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def get_success_url(self):
        return reverse_lazy('duel:player_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        messages.success(self.request, 'メンバーを更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "メンバーの更新に失敗しました。")
        return super().form_invalid(form)


class PlayerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Player
    template_name = 'player_delete.html'
    success_url = reverse_lazy('duel:player_list')

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
    template_name = 'team_create.html'
    form_class = TeamCreateForm
    success_url = reverse_lazy('duel:player_list')

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def form_valid(self, form):  # formのバリデーションに問題がなければ実行
        team = form.save(commit=False)
        team.save()
        affl = Affiliation()
        affl.team = team
        affl.user = self.request.user
        affl.save()
        self.request.user.have_team = True
        self.request.user.save()

        messages.success(self.request, "チームを作成しました。")
        return super().form_valid(form)

    def form_invalid(self, form):  # formのバリデーションに問題があるときに実行
        messages.error(self.request, "チームの作成に失敗しました。")
        return super().form_invalid(form)


class TeamConfigView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    template_name = 'team_config.html'
    form_class = TeamConfigForm

    def get_context_data(self, **kwargs):
        affl = Affiliation.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['team'] = affl.team
        return context

    def get_success_url(self):
        return reverse_lazy('duel:home')

    def form_valid(self, form):
        messages.success(self.request, 'チーム設定を更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "チーム設定の更新に失敗しました。")
        return super().form_invalid(form)

