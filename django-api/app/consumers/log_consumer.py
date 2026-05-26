import json
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
django.setup()

from events.models import EventLog
from events.consumer_base import consume_loop

logger = logging.getLogger(__name__)

TOPICS = ["match.finished", "tournament.created", "user.registered", "team.created"]


def handle_event(msg) -> None:
    topic = msg.topic()
    payload = json.loads(msg.value())

    if EventLog.objects.filter(topic=topic, payload=payload).exists():
        logger.info("Event already logged for topic %s — skipping", topic)
        return

    EventLog.objects.create(topic=topic, payload=payload)
    logger.info("Logged event on topic %s", topic)


if __name__ == "__main__":
    consume_loop("audit-log-service", TOPICS, handle_event)
