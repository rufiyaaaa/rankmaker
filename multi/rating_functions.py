import itertools
import math
from .models import Duel, Rating, Team, Player, Game, Participant


def eq_rating(old, even):
    new = [0.0, 0.0]
    mu_ba = 1 / (1 + 10 ** ((old[0] - old[1]) / 400))
    if even:
        new[0] = old[0] + 30 * (0.5 - mu_ba)
        new[1] = old[1] + 30 * (0.5 - mu_ba)
    else:
        new[0] = old[0] + 30 * mu_ba
        new[1] = old[1] - 30 * mu_ba
    return new


def calc_duel_rating(game):
    # Duelごとのレーティング変化を計算し、差分として記録する（のちに統合するため）
    duel_set = game.duel_game.all()
    for duel in duel_set:
        old_rating = [duel.winner.latest_rating(game.date), duel.loser.latest_rating(game.date)]
        new_rating = eq_rating(old_rating, duel.even)
        winner_rating_record = Rating.objects.filter(duel=duel).get(player=duel.winner)
        winner_rating_record.rating_diff = (new_rating[0] - old_rating[0]) / (game.participant_game.all().count() -1)
        winner_rating_record.save()
        loser_rating_record = Rating.objects.filter(duel=duel).get(player=duel.loser)
        loser_rating_record.rating_diff = (new_rating[1] - old_rating[1]) / (game.participant_game.all().count() -1)
        loser_rating_record.save()


def calc_game_rating(game=Game()):
    participant_set = game.participant_game.all()   # gameに紐づく参加者を列挙
    duel_set = game.duel_game.all()                 # gameに紐づくduelを列挙
    rating_set_master = Rating.objects.none()       # rating_set_masterは空っぽ
    team = game.team
    for duel in duel_set:                           # 関連するduelに対して、関連するratingを取得してrating_set_masterに追加しようとしている？
        rating_set_master = rating_set_master | duel.rating_duel.all()
    for participant in participant_set:
        rating_set = rating_set_master.filter(player=participant.player)
        old_rating = participant.player.latest_rating(game.date)
        rating_diff = 0.0
        for rating in rating_set:
            rating_diff += rating.rating_diff
        participant.new_rating = old_rating + rating_diff
        participant.old_rating = old_rating
        participant.rating_diff = rating_diff

        # 補正レーティング計算
        offset_term = team.offset_term
        participation_number = Participant.objects.filter(player=participant.player).filter(game__date__lt=participant.game.date).count() + 1
        if participation_number > offset_term:
            offset_value = 0.0
        else:
            offset_value = (2*(offset_term+1)-participation_number-1)*participation_number*500\
                       /(offset_term * (offset_term + 1))-500
        participant.new_appr = participant.new_rating + offset_value
        ones_old_participations = Participant.objects.filter(player=participant.player).filter(game__date__lt=participant.game.date)
        if ones_old_participations:
            participant.old_appr = ones_old_participations.order_by('game__date').last().new_appr
        else:
            participant.old_appr = 1000.0
        participant.appr_diff = participant.new_appr - participant.old_appr

        participant.player.ltst_rating = participant.new_appr
        participant.save()
        participant.player.save()


def rating_temp_reg(duel=Duel()):
    """duelを元に、Ratingを作成し、埋められるところを埋める。"""
    ratings = duel.rating_duel.all()
    if ratings.count() == 0:
        # 勝者のレーティングを計算せず登録
        winrate = Rating()
        winrate.duel = duel
        winrate.player = duel.winner
        winrate.save()
        # 敗者のレーティングを計算せず登録
        losrate = Rating()
        losrate.duel = duel
        losrate.player = duel.loser
        losrate.save()


def umpire(player_pair, duel=Duel()):
    """player_pairの順位差をもとに、与えられたduelに勝敗を入力する"""
    if player_pair[0][1] < player_pair[1][1]:
        duel.winner = Player.objects.get(pk=player_pair[0][0])
        duel.loser = Player.objects.get(pk=player_pair[1][0])
        duel.even = False
    elif player_pair[0][1] > player_pair[1][1]:
        duel.winner = Player.objects.get(pk=player_pair[0][0])
        duel.loser = Player.objects.get(pk=player_pair[1][0])
        duel.even = False
    else:
        duel.winner = Player.objects.get(pk=player_pair[0][0])
        duel.loser = Player.objects.get(pk=player_pair[1][0])
        duel.even = True


def duel_registration(player_pair, game):
    """Game結果から分解したDuelを検索。なければ登録する。あれば更新する。"""
    """都合がいいので同時にrating_temp_regも実行する。"""

    duel = Duel()
    duel.game = game
    umpire(player_pair, duel)  # player_pairの順位差をもとに、与えられたduelに勝敗を入力する
    duel.save()
    rating_temp_reg(duel)


def participant_registration(result, game=Game()):
    """特定のGameの結果を保存する。ratingは後ほど補完される。"""
    participant = Participant()
    participant.game = game
    participant.player = Player.objects.get(pk=result[0])
    participant.rank = result[1]
    participant.save()


def refresh_rating(game):
    """与えられたGameを計算する"""
    calc_duel_rating(game)   # Duelごとのレーティング変化量を計算
    calc_game_rating(game)   # 上記レーティング変化量からGame単位のレーティング変化量を計算し、Participantに反映
    game.need_to_recalc = False
    game.save()


def put_badge(game_calculated):
    """与えられた日時以降のGameから参加者が共通しているものを探し、要再計算をTrueにする"""
    date = game_calculated.date
    team = game_calculated.team
    participant_records = Participant.objects.filter(game=game_calculated)    # gameの参加者を取得
    competitors = set()
    for participant in participant_records:
        competitors.add(participant.player)

    future_games = Game.objects.filter(team=team).filter(date__gt=date).order_by('date')

    for game in future_games:
        comparable_competitors = set()
        comparable_participant_records = Participant.objects.filter(game=game)
        for participant in comparable_participant_records:  # レコードから集合に値を移動
            comparable_competitors.add(participant.player)

        if len(competitors & comparable_competitors) != 0:
            game.need_to_recalc = True
            game.save()


def separate(data, game=Game()):
    """GameをもとにParticipantを登録。1vs1に分解しDuelを登録しレーティングの計算を行う。"""
    rank_data = []
    for key in data:        # dataの中からkeyを取り出して、csrf, date, nameでなく、かつ・・・
        if key != 'csrfmiddlewaretoken' and key != 'date' and key != 'name':
            if data[key] != '':     # 順位が空欄でなければ
                rank_data.append([key, int(data[key])])      # 二次元配列の形でrank_dataに突っ込む。左が名前、右が順位
    rank_data.sort(key=lambda x: x[1])              # 順位でソートする
    for result in rank_data:
        participant_registration(result, game)
        # 仮のRatingレコードも↑で作成(duelを作った時にそれに対して作成するのがスマート）
    for player_pair in itertools.combinations(rank_data, 2):
        duel_registration(player_pair, game)


def separate_1on1(data, game=Game()):
    """GameをもとにParticipantを登録。1vs1に分解しDuelを登録しレーティングの計算を行う。"""

    if "even" in data:
        rank_data = [[data["winner"], 1], [data["loser"], 1]]
    else:
        rank_data = [[data["winner"], 1], [data["loser"], 2]]
        rank_data.sort(key=lambda x: x[1])              # 順位でソートする
    for result in rank_data:
        participant_registration(result, game)
        # 仮のRatingレコードも↑で作成(duelを作った時にそれに対して作成するのがスマート）
    for player_pair in itertools.combinations(rank_data, 2):
        duel_registration(player_pair, game)