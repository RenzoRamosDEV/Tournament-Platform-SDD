from django.utils import timezone


class MatchNotFound(Exception):
    pass


class MatchAlreadyFinished(Exception):
    pass


class TournamentNotFound(Exception):
    pass


class InvalidTournamentState(Exception):
    pass


K_FACTOR = 32
INITIAL_ELO = 1000


def _expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def _update_elo(winner_elo, loser_elo):
    expected_w = _expected_score(winner_elo, loser_elo)
    expected_l = _expected_score(loser_elo, winner_elo)
    new_winner = round(winner_elo + K_FACTOR * (1 - expected_w))
    new_loser = round(loser_elo + K_FACTOR * (0 - expected_l))
    return new_winner, new_loser


class MatchService:
    @staticmethod
    def report_result(match_id, winner_id, score_a, score_b, *, is_admin):
        from apps.tournaments.models import Match
        from apps.teams.models import TeamMember
        from apps.users.models import EloHistory

        try:
            match = Match.objects.select_related("team_a", "team_b").get(pk=match_id)
        except Match.DoesNotExist:
            raise MatchNotFound(f"Match {match_id} not found.")

        if match.status == "finished" and not is_admin:
            raise MatchAlreadyFinished("Match result already reported.")

        match.winner_team_id = winner_id
        match.score_a = score_a
        match.score_b = score_b
        match.status = "finished"
        match.played_at = timezone.now()
        match.save()

        MatchService._update_team_elo(match)

        from django.db import transaction
        import events.producer as _producer

        payload = {
            "match_id": match.id,
            "team_a_id": match.team_a_id,
            "team_b_id": match.team_b_id,
            "winner_id": match.winner_team_id,
            "reported_at": match.played_at.isoformat(),
        }
        transaction.on_commit(lambda: _producer.publish_event("match.finished", payload))
        return match

    @staticmethod
    def _update_team_elo(match):
        from apps.teams.models import TeamMember
        from apps.users.models import EloHistory

        winner_id = match.winner_team_id
        loser_id = match.team_a_id if winner_id == match.team_b_id else match.team_b_id

        winner_members = list(
            TeamMember.objects.select_related("user").filter(team_id=winner_id)
        )
        loser_members = list(
            TeamMember.objects.select_related("user").filter(team_id=loser_id)
        )

        elo_records = []
        for member in winner_members:
            user = member.user
            new_elo, _ = _update_elo(user.elo, INITIAL_ELO)
            elo_records.append(EloHistory(
                user=user, match=match, elo_before=user.elo, elo_after=new_elo
            ))
            user.elo = new_elo
            user.save(update_fields=["elo"])

        for member in loser_members:
            user = member.user
            _, new_elo = _update_elo(INITIAL_ELO, user.elo)
            elo_records.append(EloHistory(
                user=user, match=match, elo_before=user.elo, elo_after=new_elo
            ))
            user.elo = new_elo
            user.save(update_fields=["elo"])

        if elo_records:
            EloHistory.objects.bulk_create(elo_records)


    @staticmethod
    def _update_team_elo_by_match_id(match_id: int) -> None:
        from apps.tournaments.models import Match

        match = Match.objects.select_related("team_a", "team_b").get(pk=match_id)
        MatchService._update_team_elo(match)


class TournamentService:
    @staticmethod
    def start(tournament_id):
        from apps.tournaments.models import Tournament

        try:
            tournament = Tournament.objects.get(pk=tournament_id)
        except Tournament.DoesNotExist:
            raise TournamentNotFound(f"Tournament {tournament_id} not found.")

        if tournament.status != "open":
            raise InvalidTournamentState(
                f"Cannot start a tournament with status '{tournament.status}'. Expected 'open'."
            )

        tournament.status = "ongoing"
        tournament.save(update_fields=["status"])
        return tournament
