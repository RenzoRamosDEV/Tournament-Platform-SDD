import json
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
django.setup()

from events.models import NotificationLog
from events.consumer_base import consume_loop

logger = logging.getLogger(__name__)


def _send_notification(match_id: int, team_id: int) -> None:
    logger.info("Notification: match %s result sent to team %s", match_id, team_id)


def handle_match_finished(msg) -> None:
    payload = json.loads(msg.value())
    match_id = payload["match_id"]
    team_a_id = payload["team_a_id"]
    team_b_id = payload["team_b_id"]

    for team_id in (team_a_id, team_b_id):
        if NotificationLog.objects.filter(match_id=match_id, team_id=team_id).exists():
            logger.info("Notification already sent for match %s team %s — skipping", match_id, team_id)
            continue
        _send_notification(match_id, team_id)
        NotificationLog.objects.create(match_id=match_id, team_id=team_id)


if __name__ == "__main__":
    consume_loop("notification-service", ["match.finished"], handle_match_finished)
