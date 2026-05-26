"""
Integration test: full publish → consume → persist flow for match.finished.

Uses a fake Kafka (in-memory message passing via mocks) to verify that:
1. MatchService.report_result publishes a match.finished event
2. log_consumer.handle_event persists it to EventLog
3. ranking_consumer.handle_match_finished updates ELO
4. notification_consumer.handle_match_finished creates NotificationLog entries
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase


class MatchFinishedFlowTest(TestCase):
    def _make_fake_msg(self, topic: str, payload: dict):
        msg = MagicMock()
        msg.topic.return_value = topic
        msg.value.return_value = json.dumps(payload).encode("utf-8")
        return msg

    @patch("events.producer.publish_event")
    def test_full_publish_consume_persist(self, mock_publish):
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team, TeamMember
        from apps.users.models import User, EloHistory
        from apps.tournaments.services import MatchService
        from consumers.log_consumer import handle_event
        from consumers.ranking_consumer import handle_match_finished as ranking_handler
        from consumers.notification_consumer import handle_match_finished as notif_handler
        from events.models import EventLog, NotificationLog

        user_a = User.objects.create_user(email="fa@a.com", username="fa", password="x", elo=1000)
        user_b = User.objects.create_user(email="fb@a.com", username="fb", password="x", elo=1000)
        team_a = Team.objects.create(name="FlowA", owner=user_a)
        team_b = Team.objects.create(name="FlowB", owner=user_a)
        TeamMember.objects.create(user=user_a, team=team_a)
        TeamMember.objects.create(user=user_b, team=team_b)
        tournament = Tournament.objects.create(
            name="Flow Cup", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user_a,
        )
        match = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b,
        )

        # 1. Producer publishes the event after commit
        with self.captureOnCommitCallbacks(execute=True):
            MatchService.report_result(match.id, team_a.id, 2, 1, is_admin=False)

        assert mock_publish.called
        published_topic, published_payload = mock_publish.call_args[0]
        assert published_topic == "match.finished"

        # 2. Simulate consumers receiving the message
        fake_msg = self._make_fake_msg("match.finished", published_payload)

        handle_event(fake_msg)
        ranking_handler(fake_msg)
        notif_handler(fake_msg)

        # 3. log-consumer persisted the event
        assert EventLog.objects.filter(topic="match.finished").count() == 1

        # 4. ranking-consumer updated ELO for both teams
        assert EloHistory.objects.filter(match=match).count() == 2

        # 5. notification-consumer created notification records
        assert NotificationLog.objects.filter(match=match).count() == 2
