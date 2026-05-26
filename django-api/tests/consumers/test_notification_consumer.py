import json
from unittest.mock import MagicMock

import pytest


def _make_msg(payload: dict):
    msg = MagicMock()
    msg.value.return_value = json.dumps(payload).encode("utf-8")
    return msg


@pytest.mark.django_db
class NotificationConsumerTest:
    def test_notification_dispatched_to_both_teams(self):
        from consumers.notification_consumer import handle_match_finished
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team
        from apps.users.models import User
        from events.models import NotificationLog

        user = User.objects.create_user(email="nc@a.com", username="nc_player", password="x")
        team_a = Team.objects.create(name="NotiA", owner=user)
        team_b = Team.objects.create(name="NotiB", owner=user)
        tournament = Tournament.objects.create(
            name="NT1", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user,
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

        assert NotificationLog.objects.filter(match_id=match.id).count() == 2

    def test_duplicate_event_is_idempotent(self):
        from consumers.notification_consumer import handle_match_finished
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team
        from apps.users.models import User
        from events.models import NotificationLog

        user = User.objects.create_user(email="nd@a.com", username="nd_player", password="x")
        team_a = Team.objects.create(name="NotiC", owner=user)
        team_b = Team.objects.create(name="NotiD", owner=user)
        tournament = Tournament.objects.create(
            name="NT2", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user,
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
        handle_match_finished(msg)

        assert NotificationLog.objects.filter(match_id=match.id).count() == 2
