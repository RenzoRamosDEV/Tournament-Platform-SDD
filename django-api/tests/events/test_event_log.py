import pytest
from django.utils import timezone


@pytest.mark.django_db
class EventLogModelTest:
    def test_topic_field_is_char(self):
        from events.models import EventLog

        log = EventLog.objects.create(topic="match.finished", payload={"match_id": 1})
        assert log.topic == "match.finished"

    def test_payload_stored_as_json(self):
        from events.models import EventLog

        data = {"match_id": 42, "winner_id": 7}
        log = EventLog.objects.create(topic="match.finished", payload=data)
        refreshed = EventLog.objects.get(pk=log.pk)
        assert refreshed.payload == data

    def test_received_at_is_set_automatically(self):
        from events.models import EventLog

        before = timezone.now()
        log = EventLog.objects.create(topic="team.created", payload={"team_id": 3})
        after = timezone.now()
        assert before <= log.received_at <= after

    def test_received_at_is_not_null(self):
        from events.models import EventLog

        log = EventLog.objects.create(topic="user.registered", payload={"user_id": 1})
        assert log.received_at is not None

    def test_str_representation(self):
        from events.models import EventLog

        log = EventLog(topic="tournament.created", payload={})
        assert "tournament.created" in str(log)
