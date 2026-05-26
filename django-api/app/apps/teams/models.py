from django.conf import settings
from django.db import models
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    elo = models.IntegerField(default=1000, db_index=True)
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


class EloHistory(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, db_column="team_id", related_name="elo_history"
    )
    match = models.ForeignKey(
        "tournaments.Match",
        on_delete=models.CASCADE,
        db_column="match_id",
        related_name="team_elo_history",
    )
    elo_before = models.IntegerField()
    elo_after = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "team_elo_history"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "match"], name="team_elo_history_unique_team_match"
            )
        ]
        indexes = [
            models.Index(fields=["team"], name="team_elo_history_team_idx"),
            models.Index(fields=["match"], name="team_elo_history_match_idx"),
        ]

    def __str__(self):
        return f"{self.team} match={self.match_id}: {self.elo_before}→{self.elo_after}"
