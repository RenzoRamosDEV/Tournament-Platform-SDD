import json
import logging
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
django.setup()

from apps.users.models import EloHistory
from apps.tournaments.services import MatchService
from events.consumer_base import consume_loop

logger = logging.getLogger(__name__)


def handle_match_finished(msg) -> None:
    payload = json.loads(msg.value())
    match_id = payload["match_id"]

    if EloHistory.objects.filter(match_id=match_id).exists():
        logger.info("ELO already calculated for match %s — skipping", match_id)
        return

    MatchService._update_team_elo_by_match_id(match_id)
    logger.info("ELO updated for match %s", match_id)


if __name__ == "__main__":
    consume_loop("ranking-service", ["match.finished"], handle_match_finished)
