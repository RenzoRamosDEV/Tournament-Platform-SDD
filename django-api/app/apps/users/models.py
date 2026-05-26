from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, username, password, role="player", elo=1000, **extra):
        from django.db import transaction
        import events.producer as _producer

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, elo=elo, **extra)
        user.set_password(password)
        user.save(using=self._db)

        payload = {
            "user_id": user.id,
            "email": user.email,
            "registered_at": user.created_at.isoformat(),
        }
        transaction.on_commit(lambda: _producer.publish_event("user.registered", payload))
        return user

    def create_superuser(self, email, username, password, **extra):
        extra.setdefault("role", "admin")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("admin", "admin"), ("organizer", "organizer"), ("player", "player")]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="player")
    elo = models.IntegerField(default=1000)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["-elo"], name="users_elo_desc_idx")]


class EloHistory(models.Model):
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, db_column="user_id"
    )
    match = models.ForeignKey(
        'tournaments.Match', on_delete=models.CASCADE, db_column="match_id"
    )
    elo_before = models.IntegerField()
    elo_after = models.IntegerField()
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "elo_history"
