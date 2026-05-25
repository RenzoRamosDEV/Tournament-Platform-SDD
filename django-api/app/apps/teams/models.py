from django.conf import settings
from django.db import models
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="owner_id",
        related_name="owned_teams",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "teams"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, db_column="team_id")
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "team_members"
        constraints = [
            models.UniqueConstraint(fields=["user", "team"], name="team_members_pk")
        ]

    def __str__(self):
        return f"{self.user} in {self.team}"
