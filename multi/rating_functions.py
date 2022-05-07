from .models import Duel, Rating, Team, Player, Game, Participant


def eq_rating(old, even):
    new = [0.0, 0.0]
    mu = 1 / (1 + 10 ** ((old[0] - old[1]) / 400))
    if even:
        new[0] = old[0] + 30 * (0.5 - mu)
        new[1] = old[1] + 30 * (0.5 - mu)
    else:
        new[0] = old[0] + 30 * (1 - mu)
        new[1] = old[1] - 30 * mu
    return new


def calc_duel_rating(game=Game()):   # Duelごとのレーティング変化を計算し、差分として記録する（のちに統合するため）
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
        participant.save()


def rating_temp_reg(duel=Duel()):
    """duelを元に、Ratingを作成し、埋められるところを埋める。"""
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


def duel_registration(player_pair, game):
    """Game結果から分解したDuelを登録する。都合がいいので同時にrating_temp_regも実行する。"""
    # update実装時に、再構成する気がする
    duel = Duel()  # ここの一連の処理は外に出してもいいかも
    duel.game = game
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
        calc_duel_rating(game)   # Duelごとのレーティング変化量を計算
        calc_game_rating(game)   # 上記レーティング変化量からGame単位のレーティング変化量を計算し、Participantに反映

