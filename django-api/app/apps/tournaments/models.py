from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Tournament(models.Model):
    STATUS_CHOICES = [
        ("draft", "draft"),
        ("open", "open"),
        ("ongoing", "ongoing"),
        ("finished", "finished"),
    ]
    FORMAT_CHOICES = [
        ("single_elimination", "single_elimination"),
        ("round_robin", "round_robin"),
    ]

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    max_teams = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="created_by_id",
        related_name="created_tournaments",
    )

    class Meta:
        db_table = "tournaments"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "open", "ongoing", "finished"]),
                name="tournaments_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(format__in=["single_elimination", "round_robin"]),
                name="tournaments_format_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(max_teams__gt=0),
                name="tournaments_max_teams_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="tournaments_end_date_gte_start_date",
            ),
        ]


class TournamentTeam(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, db_column="tournament_id"
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.CASCADE, db_column="team_id"
    )
    registered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tournament_teams"
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "team"], name="tournament_teams_pk"
            )
        ]

    def __str__(self):
        return f"{self.team} in {self.tournament}"


class Match(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "scheduled"),
        ("ongoing", "ongoing"),
        ("finished", "finished"),
    ]

    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, db_column="tournament_id", related_name="matches"
    )
    team_a = models.ForeignKey(
        'teams.Team', on_delete=models.PROTECT, db_column="team_a_id", related_name="matches_as_a"
    )
    team_b = models.ForeignKey(
        'teams.Team', on_delete=models.PROTECT, db_column="team_b_id", related_name="matches_as_b"
    )
    winner_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="winner_team_id",
        related_name="won_matches",
    )
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="scheduled")
    played_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.status == "finished":
            if self.winner_team is None:
                raise ValidationError("A finished match must have a winner.")
            if self.winner_team_id not in (self.team_a_id, self.team_b_id):
                raise ValidationError("winner_team must be team_a or team_b.")

    class Meta:
        db_table = "matches"
        indexes = [
            models.Index(fields=["tournament"], name="matches_tournament_idx"),
            models.Index(fields=["played_at"], name="matches_played_at_idx"),
        ]

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} [{self.status}]"
