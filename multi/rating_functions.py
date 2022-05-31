import itertools
import math
from .models import Duel, Rating, Team, Player, Game, Participant


def eq_rating(old, even):
    new = [0.0, 0.0]
    mu_01 = 1 / (1 + 10 ** ((old[0] - old[1]) / 400))
    mu_10 = 1 / (1 + 10 ** ((old[1] - old[0]) / 400))
    if even:
        new[0] = old[0] + 30 * (0.5 - mu_01)
        new[1] = old[1] + 30 * (0.5 - mu_10)
    else:
        new[0] = old[0] + 30 * (1 - mu_01)
        new[1] = old[1] - 30 * mu_10
    return new


def calc_duel_rating(game=Game()):
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
        print('duel' + duel.__str__() + '勝者' + duel.winner.name + "  敗者" + duel.loser.name)


def calc_game_rating(game=Game()):
    participant_set = game.participant_game.all()
    duel_set = game.duel_game.all()
    rating_set_master = Rating.objects.none()
    for duel in duel_set:
        rating_set_master = rating_set_master | duel.rating_duel.all()
    for participant in participant_set:
        rating_set = rating_set_master.filter(player=participant.player)
        old_rating = participant.player.latest_rating(game.date)
        rating_diff = 0.0
        for rating in rating_set:
            rating_diff += rating.rating_diff
        participant.new_rating = old_rating + rating_diff
        participant.player.ltst_rating = math.floor(participant.new_rating)
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


def refresh_rating(date, team):
    """与えられた日時以降のGameを列挙し、早いものから順に再計算をかける"""
    game_set = Game.objects.filter(team=team).filter(date__gte=date).order_by('date')
    for game in game_set:
        print("■" + game.__str__() + 'のレーティングを計算')
        calc_duel_rating(game)   # Duelごとのレーティング変化量を計算
        print(game.__str__() + 'のレーティングをParticipantに反映')
        calc_game_rating(game)   # 上記レーティング変化量からGame単位のレーティング変化量を計算し、Participantに反映

        print('■計算完了')


# def participant_update(rank_data, game=Game()):
#     old_participants = game.participant_game.all()
#     check_list = []
#     for participant in old_participants:
#         check_list.append(participant.player)
#     for result in rank_data:
#         player = Player.objects.get(pk=result[0])
#         if old_participants.filter(player=player).count() == 1:
#             record = old_participants.get(player=player)
#             record.rank = result[1]
#             record.save()
#             check_list.remove(player)
#         else:
#             participant_registration(result, game)
#     if len(check_list) != 0:
#         for player in check_list:
#             old_participants.get(player=player).delete()


def separate(data, game=Game()):
    """GameをもとにParticipantを登録。1vs1に分解しDuelを登録しレーティングの計算を行う。"""
    rank_data = []
    for key in data:
        if key != 'csrfmiddlewaretoken' and key != 'date' and key != 'name':
            if data[key] != '':
                rank_data.append([key, data[key]])
    rank_data.sort(key=lambda x: x[1])
    for result in rank_data:
        participant_registration(result, game)
        # 仮のRatingレコードも↑で作成(duelを作った時にそれに対して作成するのがスマート）
    for player_pair in itertools.combinations(rank_data, 2):
        duel_registration(player_pair, game)
