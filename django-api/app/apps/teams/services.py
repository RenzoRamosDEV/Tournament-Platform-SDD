from django.db import transaction


def calculate_elo(elo_winner: int, elo_loser: int, k: int = 32) -> tuple[int, int]:
    expected_winner = 1 / (1 + 10 ** ((elo_loser - elo_winner) / 400))
    expected_loser = 1 - expected_winner
    new_winner = round(elo_winner + k * (1 - expected_winner))
    new_loser = round(elo_loser + k * (0 - expected_loser))
    return new_winner, new_loser


@transaction.atomic
def update_elo(match) -> None:
    from apps.teams.models import EloHistory

    if EloHistory.objects.filter(match_id=match.pk).exists():
        return

    from apps.teams.models import Team

    team_ids = sorted([match.winner_team_id, _loser_id(match)])
    teams = {t.pk: t for t in Team.objects.select_for_update().filter(pk__in=team_ids).order_by("pk")}

    winner = teams[match.winner_team_id]
    loser = teams[_loser_id(match)]

    winner_elo_before = winner.elo
    loser_elo_before = loser.elo

    new_winner_elo, new_loser_elo = calculate_elo(winner.elo, loser.elo)

    winner.elo = new_winner_elo
    winner.save(update_fields=["elo"])

    loser.elo = new_loser_elo
    loser.save(update_fields=["elo"])

    EloHistory.objects.create(
        team=winner,
        match=match,
        elo_before=winner_elo_before,
        elo_after=new_winner_elo,
    )
    EloHistory.objects.create(
        team=loser,
        match=match,
        elo_before=loser_elo_before,
        elo_after=new_loser_elo,
    )


def _loser_id(match) -> int:
    return match.team_a_id if match.winner_team_id == match.team_b_id else match.team_b_id
