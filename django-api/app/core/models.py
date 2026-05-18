from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password, role="player", elo=1000, **extra):
        user = self.model(username=username, role=role, elo=elo, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra):
        extra.setdefault("role", "admin")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("admin", "admin"), ("player", "player")]

    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    elo = models.IntegerField(default=1000)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["-elo"], name="users_elo_desc_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["admin", "player"]),
                name="users_role_valid",
            )
        ]


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(
        User, on_delete=models.RESTRICT, db_column="owner_id", related_name="owned_teams"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "teams"


class TeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column="user_id")
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, db_column="team_id")
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "team_members"
        constraints = [
            models.UniqueConstraint(fields=["user", "team"], name="team_members_pk")
        ]


class Tournament(models.Model):
    STATUS_CHOICES = [
        ("draft", "draft"),
        ("open", "open"),
        ("ongoing", "ongoing"),
        ("finished", "finished"),
    ]
    FORMAT_CHOICES = [
        ("single_elim", "single_elim"),
        ("round_robin", "round_robin"),
    ]

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    max_teams = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = "tournaments"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "open", "ongoing", "finished"]),
                name="tournaments_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(format__in=["single_elim", "round_robin"]),
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
        Tournament, on_delete=models.RESTRICT, db_column="tournament_id"
    )
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, db_column="team_id")
    registered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tournament_teams"
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "team"], name="tournament_teams_pk"
            )
        ]


class Match(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("ongoing", "ongoing"),
        ("finished", "finished"),
    ]

    tournament = models.ForeignKey(
        Tournament, on_delete=models.RESTRICT, db_column="tournament_id", related_name="matches"
    )
    team_a = models.ForeignKey(
        Team, on_delete=models.RESTRICT, db_column="team_a_id", related_name="matches_as_a"
    )
    team_b = models.ForeignKey(
        Team, on_delete=models.RESTRICT, db_column="team_b_id", related_name="matches_as_b"
    )
    winner_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="winner_team_id",
        related_name="matches_won",
    )
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    played_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "matches"
        indexes = [
            models.Index(fields=["tournament"], name="matches_tournament_idx"),
            models.Index(fields=["played_at"], name="matches_played_at_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "ongoing", "finished"]),
                name="matches_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(winner_team__isnull=True)
                    | models.Q(winner_team=models.F("team_a"))
                    | models.Q(winner_team=models.F("team_b"))
                ),
                name="matches_winner_valid",
            ),
        ]
