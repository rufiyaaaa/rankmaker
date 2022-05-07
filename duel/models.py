from django.utils import timezone
from datetime import datetime
from accounts.models import CustomUser
from django.db import models


class Team(models.Model):
    """チームモデル"""

    name = models.CharField(verbose_name='本文', max_length=50, blank=True, null=True)
    est_date = models.DateTimeField(verbose_name='登録日', auto_now_add=True)
    description = models.TextField(verbose_name='説明', max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Team'

    def __str__(self):
        return self.name


class Player(models.Model):
    """プレイヤーモデル"""

    team = models.ForeignKey(Team, verbose_name='所属', on_delete=models.PROTECT)
    name = models.CharField(verbose_name='プレイヤー', max_length=40)
    inactive = models.BooleanField(verbose_name='引退', default=False, blank=True)
    latest_rating = models.FloatField(verbose_name='最新レーティング', default=0)

    class Meta:
        verbose_name_plural = 'Player'

    def match_exp(self):
        return Rating.objects.filter(player=self).count()

    def __str__(self):
        return format(self.name)


class Affiliation(models.Model):
    """所属モデル"""
    user = models.ForeignKey(CustomUser, verbose_name='ユーザー', on_delete=models.PROTECT, related_name="duel_affl_user")
    team = models.ForeignKey(Team, verbose_name='チーム', on_delete=models.PROTECT, related_name="duel_affl_team")

    class Meta:
        verbose_name_plural = 'Affiliations'

    def __str__(self):
        return format(self.user) + " belongs to " + format(self.team)


class Match(models.Model):
    """マッチモデル"""

    name = models.CharField(verbose_name='対戦名', max_length=50, default=timezone.now)
    team = models.ForeignKey(Team, verbose_name='チーム', on_delete=models.PROTECT, related_name="Team_ID")
    winner = models.ForeignKey(Player, verbose_name='勝者', on_delete=models.PROTECT, related_name="Winner_ID")
    loser = models.ForeignKey(Player, verbose_name='敗者', on_delete=models.PROTECT, related_name="Loser_ID")
    even = models.BooleanField(verbose_name='引き分け')
    date = models.DateTimeField(verbose_name='試合日時', default=timezone.now)
    comment = models.TextField(verbose_name='コメント', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Match'

    def winner_new_rating(self):
        return Rating.objects.filter(match=self.id).get(player=self.winner).rating

    def loser_new_rating(self):
        return Rating.objects.filter(match=self.id).get(player=self.loser).rating

    def winner_old_rating(self):
        winner_ratings = Rating.objects.filter(player=self.winner)
        date_cursor = Match.objects.order_by('date').first().date
        winner_old_rating = 1500.0
        for query in winner_ratings:
            if query.match.date < self.date:
                if date_cursor <= query.match.date:
                    winner_old_rating = query.rating
                    date_cursor = query.match.date
        return winner_old_rating

    def loser_old_rating(self):
        loser_ratings = Rating.objects.filter(player=self.loser)
        date_cursor = Match.objects.order_by('date').first().date
        loser_old_rating = 1500.0
        for query in loser_ratings:
            if query.match.date < self.date:
                if date_cursor <= query.match.date:
                    loser_old_rating = query.rating
                    date_cursor = query.match.date
        return loser_old_rating

    def winner_new_rating_disp(self):
        return Rating.objects.filter(match=self.id).get(player=self.winner).appr_rating

    def winner_old_rating_disp(self):
        winner_ratings = Rating.objects.filter(player=self.winner)
        date_cursor = Match.objects.order_by('date').first().date
        winner_old_rating = 0
        for query in winner_ratings:
            if query.match.date < self.date:
                if date_cursor <= query.match.date:
                    winner_old_rating = query.appr_rating
                    date_cursor = query.match.date
        return winner_old_rating

    def loser_new_rating_disp(self):
        return Rating.objects.filter(match=self.id).get(player=self.loser).appr_rating

    def loser_old_rating_disp(self):
        loser_ratings = Rating.objects.filter(player=self.loser)
        date_cursor = Match.objects.order_by('date').first().date
        loser_old_rating = 0
        for query in loser_ratings:
            if query.match.date < self.date:
                if date_cursor <= query.match.date:
                    loser_old_rating = query.appr_rating
                    date_cursor = query.match.date
        return loser_old_rating

    def __str__(self):
        return format(self.id) + format(self.winner) + "-" + format(self.loser)


class Rating(models.Model):
    """レーティングモデル"""

    player = models.ForeignKey(Player, verbose_name='プレイヤー', on_delete=models.PROTECT)
    match = models.ForeignKey(Match, verbose_name='マッチ', on_delete=models.CASCADE, related_name='arg_match')
    rating = models.FloatField(verbose_name='レーティング', default=1500.0)
    appr_rating = models.FloatField(verbose_name='見掛けのレーティング', default=0)

    class Meta:
        verbose_name_plural = 'Rating'

    def __str__(self):
        return format(self.player.name) + format(self.match.date, '%Y%m%d%H')
