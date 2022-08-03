from django.utils import timezone
from datetime import datetime

from django.utils.timezone import make_aware

from accounts.models import CustomUser
from django.db import models

from django.core.validators import MinLengthValidator, RegexValidator

# Create your models here.


class Team(models.Model):
    """チームモデル"""

    name = models.CharField(verbose_name='チーム名', max_length=50, default="<チーム名>")
    est_date = models.DateTimeField(verbose_name='登録日', auto_now_add=True)
    description = models.TextField(verbose_name='説明', max_length=500, blank=True, null=True)
    page_id = models.CharField(
        verbose_name="キーフレーズ",
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        validators=[
            MinLengthValidator(5, '5文字以上で設定してください'),
            RegexValidator(r'^[a-zA-Z0-9]*$', '使用可能な文字は半角英数字のみです')
        ]
    )

    class Meta:
        verbose_name_plural = 'Team'

    def __str__(self):
        return self.name


class Player(models.Model):
    """プレイヤーモデル"""

    team = models.ForeignKey(Team, verbose_name='所属', on_delete=models.CASCADE)
    name = models.CharField(verbose_name='プレイヤー', max_length=10000)
    inactive = models.BooleanField(verbose_name='引退', default=False, blank=True)
    ltst_rating = models.IntegerField(verbose_name='最新レーティング', default=0)

    class Meta:
        verbose_name_plural = 'Player'

    def match_exp(self):
        return Participant.objects.filter(player=self).count()

    def latest_rating(self, date):  # Participantを探って最新のレーティングを見つける
        records = Participant.objects.filter(player=self)
        date_cursor = date
        latest_participant = records.first()
        for record in records:
            if record.game.date < date_cursor:
                date_cursor = record.game.date
                latest_participant = record

        if date_cursor == date:
            return 1500.0
        else:
            for record in records:
                if record.game.date < date:
                    if date_cursor < record.game.date:
                        date_cursor = record.game.date
                        latest_participant = record
            return float(latest_participant.new_rating)

    def now_rating(self):
        return self.latest_rating(make_aware(datetime.now()))

    def __str__(self):
        return format(self.name) + " (" + format(self.team.name) + ")"


class Affiliation(models.Model):
    """所属モデル"""
    user = models.ForeignKey(CustomUser, verbose_name='ユーザー', on_delete=models.CASCADE, related_name="br_affl_user")
    team = models.ForeignKey(Team, verbose_name='チーム', on_delete=models.CASCADE, related_name="duel_affl_team")

    class Meta:
        verbose_name_plural = 'Affiliations'

    def __str__(self):
        return format(self.user) + " (" + format(self.team) + ")"


class Game(models.Model):
    """ゲームモデル"""
    name = models.CharField(verbose_name='試合名称', max_length=50, blank=True, null=True)
    team = models.ForeignKey(Team, verbose_name='チーム', on_delete=models.CASCADE)
    date = models.DateTimeField(verbose_name='試合日時', default=datetime.now)

    class Meta:
        verbose_name_plural = 'Game'

    def __str__(self):
        return format(self.id) +":"+ format(self.date, '%m%d') + "(" + format(self.team) + ")"


class Participant(models.Model):
    """Gameの参加者を追加するモデル"""
    game = models.ForeignKey(
        Game,
        verbose_name='ゲーム',
        on_delete=models.CASCADE,
        related_name='participant_game'
    )
    player = models.ForeignKey(
        Player,
        verbose_name='player',
        on_delete=models.PROTECT,
        related_name='participant_player'
    )
    rank = models.IntegerField(verbose_name='順位', default=0)
    new_rating = models.FloatField(verbose_name='対戦後のレーティング', default=1500.0)
    appr_rating = models.IntegerField(verbose_name='修正レーティング', default=0)

    class Meta:
        verbose_name_plural = 'Participants'

    def __str__(self):
        return format(self.game.id) + ":" + format(self.player) \
               + " pos: " + format(self.rank) + " R:" + format(self.new_rating)


class Duel(models.Model):
    """Gameを分解した一対一対戦"""
    game = models.ForeignKey(Game, verbose_name='対応するGame', on_delete=models.CASCADE, related_name='duel_game')
    winner = models.ForeignKey(Player, verbose_name='勝者', on_delete=models.PROTECT, related_name='duel_win')
    loser = models.ForeignKey(Player, verbose_name='敗者', on_delete=models.PROTECT, related_name='duel_los')
    even = models.BooleanField(verbose_name='引き分け')

    class Meta:
        verbose_name_plural = 'Duel'

    def __str__(self):

        return format(self.game.id) + ": " + format(self.winner.name) + "-" + format(self.loser) \
               + "(" + format(self.even) + ")"


class Rating(models.Model):
    """レーティングモデル"""

    player = models.ForeignKey(Player, verbose_name='プレイヤー', on_delete=models.PROTECT)
    duel = models.ForeignKey(Duel, verbose_name='マッチ', on_delete=models.CASCADE, related_name='rating_duel')
    rating_diff = models.FloatField(verbose_name='レーティング差分', default=0.0)

    class Meta:
        verbose_name_plural = 'Rating'

    def __str__(self):
        return format(self.player.name) + "(" + format(self.rating_diff) + ") @" + format(self.duel.game)


class Notice(models.Model):
    """お知らせ"""
    category_choices = (
        (1, 'お知らせ'),
        (2, '重要'),
    )

    title = models.CharField(verbose_name='タイトル', max_length=50)
    text = models.TextField(verbose_name='本文')
    release_date = models.DateTimeField(verbose_name='公開日', default=datetime.now)
    category = models.IntegerField(choices=category_choices, default=1)

    def __str__(self):
        return self.title
