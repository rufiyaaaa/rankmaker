from .models import Match, Rating, Team


def eq_rating(old, even):
    new = old
    mu = 1 / (1 + 10 ** ((old[0] - old[1]) / 400))
    if even:
        new[0] = old[0] + 30 * (0.5 - mu)
        new[1] = old[1] + 30 * (0.5 - mu)
    else:
        new[0] = old[0] + 30 * (1 - mu)
        new[1] = old[1] - 30 * mu
    return new


def calc_rating(match=Match()):
    old_rating = [match.winner_old_rating(), match.loser_old_rating()]
    new_rating = eq_rating(old_rating, match.even)
    winner_rating = Rating.objects.filter(match=match).get(player=match.winner)
    winner_rating.rating = new_rating[0]
    winner_match_exp = 0
    for record in Rating.objects.filter(player=match.winner):
        if record.match.date <= match.date:
            winner_match_exp += 1
    winner_rating.appr_rating = int(new_rating[0] * min(winner_match_exp, 20) / 20)
    winner_rating.save()
    loser_rating = Rating.objects.filter(match=match).get(player=match.loser)
    loser_rating.rating = new_rating[1]
    loser_match_exp = 0
    for record in Rating.objects.filter(player=match.loser):
        if record.match.date <= match.date:
            loser_match_exp += 1
    loser_rating.appr_rating = int(new_rating[1] * min(loser_match_exp, 20) / 20)
    loser_rating.save()
    match.winner.latest_rating = winner_rating.appr_rating
    match.winner.save()
    match.loser.latest_rating = loser_rating.appr_rating
    match.loser.save()


def refresh_ratings(team=Team()):
    for match_cursor in Match.objects.filter(team=team).order_by('date'):
        calc_rating(match_cursor)