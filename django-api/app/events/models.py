from django.db import models
from django.utils import timezone


class EventLog(models.Model):
    topic = models.CharField(max_length=200)
    payload = models.JSONField()
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "event_log"

    def __str__(self):
        return f"{self.topic} @ {self.received_at}"


class NotificationLog(models.Model):
    match = models.ForeignKey(
        "tournaments.Match", on_delete=models.CASCADE, db_column="match_id"
    )
    team = models.ForeignKey(
        "teams.Team", on_delete=models.CASCADE, db_column="team_id"
    )
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notification_log"
        constraints = [
            models.UniqueConstraint(
                fields=["match", "team"], name="notification_log_match_team_unique"
            )
        ]
