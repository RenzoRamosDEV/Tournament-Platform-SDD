import json
from unittest.mock import MagicMock

import pytest


def _make_msg(topic: str, payload: dict):
    msg = MagicMock()
    msg.topic.return_value = topic
    msg.value.return_value = json.dumps(payload).encode("utf-8")
    return msg


@pytest.mark.django_db
class LogConsumerTest:
    def test_event_persisted_for_each_topic(self):
        from consumers.log_consumer import handle_event
        from events.models import EventLog

        messages = [
            _make_msg("match.finished", {"match_id": 1}),
            _make_msg("tournament.created", {"tournament_id": 2}),
            _make_msg("user.registered", {"user_id": 3}),
            _make_msg("team.created", {"team_id": 4}),
        ]

        for msg in messages:
            handle_event(msg)

        assert EventLog.objects.count() == 4
        topics = set(EventLog.objects.values_list("topic", flat=True))
        assert topics == {"match.finished", "tournament.created", "user.registered", "team.created"}

    def test_correct_payload_stored(self):
        from consumers.log_consumer import handle_event
        from events.models import EventLog

        msg = _make_msg("match.finished", {"match_id": 99, "winner_id": 7})
        handle_event(msg)

        log = EventLog.objects.get(topic="match.finished")
        assert log.payload["match_id"] == 99

    def test_received_at_is_set(self):
        from consumers.log_consumer import handle_event
        from events.models import EventLog

        msg = _make_msg("team.created", {"team_id": 5})
        handle_event(msg)

        log = EventLog.objects.get(topic="team.created")
        assert log.received_at is not None

    def test_duplicate_event_is_idempotent(self):
        from consumers.log_consumer import handle_event
        from events.models import EventLog

        msg = _make_msg("match.finished", {"match_id": 11})
        handle_event(msg)
        handle_event(msg)

        assert EventLog.objects.filter(topic="match.finished").count() == 1
