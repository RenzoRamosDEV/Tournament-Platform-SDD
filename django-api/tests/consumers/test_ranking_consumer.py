import json
from unittest.mock import MagicMock

import pytest


def _make_msg(payload: dict):
    msg = MagicMock()
    msg.value.return_value = json.dumps(payload).encode("utf-8")
    return msg


@pytest.mark.django_db
class RankingConsumerTest:
    def test_elo_recalculation_triggered_for_both_teams(self):
        from consumers.ranking_consumer import handle_match_finished
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team, TeamMember
        from apps.users.models import User, EloHistory

        user_a = User.objects.create_user(email="ra@a.com", username="ra", password="x", elo=1200)
        user_b = User.objects.create_user(email="rb@a.com", username="rb", password="x", elo=1100)
        team_a = Team.objects.create(name="RankA", owner=user_a)
        team_b = Team.objects.create(name="RankB", owner=user_a)
        TeamMember.objects.create(user=user_a, team=team_a)
        TeamMember.objects.create(user=user_b, team=team_b)
        tournament = Tournament.objects.create(
            name="RT1", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user_a,
        )
        match = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b,
            status="finished", winner_team=team_a,
        )

        msg = _make_msg({
            "match_id": match.id,
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "winner_id": team_a.id,
        })
        handle_match_finished(msg)

        assert EloHistory.objects.filter(match=match).count() == 2

    def test_duplicate_event_is_idempotent(self):
        from consumers.ranking_consumer import handle_match_finished
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team, TeamMember
        from apps.users.models import User, EloHistory

        user_a = User.objects.create_user(email="ia@a.com", username="ia", password="x", elo=1000)
        user_b = User.objects.create_user(email="ib@a.com", username="ib", password="x", elo=1000)
        team_a = Team.objects.create(name="IdemA", owner=user_a)
        team_b = Team.objects.create(name="IdemB", owner=user_a)
        TeamMember.objects.create(user=user_a, team=team_a)
        TeamMember.objects.create(user=user_b, team=team_b)
        tournament = Tournament.objects.create(
            name="IT1", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user_a,
        )
        match = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b,
            status="finished", winner_team=team_a,
        )

        msg = _make_msg({
            "match_id": match.id,
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "winner_id": team_a.id,
        })
        handle_match_finished(msg)
        elo_a_after_first = User.objects.get(pk=user_a.pk).elo

        handle_match_finished(msg)
        elo_a_after_second = User.objects.get(pk=user_a.pk).elo

        assert elo_a_after_first == elo_a_after_second
        assert EloHistory.objects.filter(match=match).count() == 2
