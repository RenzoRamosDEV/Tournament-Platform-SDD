import datetime
import importlib

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.teams.models import Team, TeamMember
from apps.tournaments.models import Match, Tournament, TournamentTeam
from apps.users.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_counter = 0


def _uid():
    global _counter
    _counter += 1
    return _counter


def make_user(role="player", **kwargs):
    n = _uid()
    defaults = dict(username=f"u{n}", email=f"u{n}@test.com", role=role)
    defaults.update(kwargs)
    return User.objects.create_user(password="secret", **defaults)


def make_team(name=None, owner=None):
    if owner is None:
        owner = make_user()
    return Team.objects.create(name=name or f"Team{_uid()}", owner=owner)


def make_tournament(status="open", created_by=None):
    if created_by is None:
        created_by = make_user(role="admin")
    return Tournament.objects.create(
        name=f"Cup{_uid()}",
        format="round_robin",
        max_teams=8,
        start_date=datetime.date(2026, 6, 1),
        end_date=datetime.date(2026, 6, 30),
        status=status,
        created_by=created_by,
    )


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Router registration smoke test
# ---------------------------------------------------------------------------

class RouterRegistrationTest(TestCase):
    """Verify all list endpoints are reachable by anonymous clients."""

    LIST_URLS = [
        "user-list",
        "team-list",
        "tournament-list",
        "match-list",
    ]

    def test_list_endpoints_return_200(self):
        for name in self.LIST_URLS:
            with self.subTest(url_name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"{name} returned {response.status_code}")


# ---------------------------------------------------------------------------
# User List API
# ---------------------------------------------------------------------------

class UserListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("user-list")
        self.user = make_user()

    def test_public_access_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_pagination_envelope_present(self):
        response = self.client.get(self.url)
        data = response.json()
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, data)

    def test_response_fields_correct(self):
        response = self.client.get(self.url)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        item = results[0]
        for field in ("id", "username", "email", "role", "elo", "avatar_url", "created_at"):
            self.assertIn(field, item)

    def test_password_not_exposed(self):
        response = self.client.get(self.url)
        results = response.json()["results"]
        for item in results:
            self.assertNotIn("password", item)


# ---------------------------------------------------------------------------
# User role filter
# ---------------------------------------------------------------------------

class UserRoleFilterTest(TestCase):
    def setUp(self):
        self.url = reverse("user-list")
        self.admin = make_user(role="admin")
        self.player = make_user(role="player")
        self.organizer = make_user(role="organizer")

    def test_admin_filter_by_valid_role(self):
        client = auth_client(self.admin)
        response = client.get(self.url, {"role": "player"})
        self.assertEqual(response.status_code, 200)
        for u in response.json()["results"]:
            self.assertEqual(u["role"], "player")

    def test_non_admin_role_filter_returns_403(self):
        client = auth_client(self.player)
        response = client.get(self.url, {"role": "player"})
        self.assertEqual(response.status_code, 403)

    def test_admin_invalid_role_returns_400(self):
        client = auth_client(self.admin)
        response = client.get(self.url, {"role": "superuser"})
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# Throttling & custom exception handler
# ---------------------------------------------------------------------------

class ThrottleExceptionHandlerTest(TestCase):
    def setUp(self):
        self.url = reverse("user-list")

    def test_throttled_returns_429_with_structured_body(self):
        from unittest.mock import patch
        with patch("rest_framework.throttling.SimpleRateThrottle.allow_request", return_value=False), \
             patch("rest_framework.throttling.SimpleRateThrottle.wait", return_value=60.0):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertEqual(data["error"], "rate_limit_exceeded")
        self.assertIn("message", data)
        self.assertIn("retry_after_seconds", data)

    def test_retry_after_seconds_is_ceiling_integer(self):
        from unittest.mock import patch
        with patch("rest_framework.throttling.SimpleRateThrottle.allow_request", return_value=False), \
             patch("rest_framework.throttling.SimpleRateThrottle.wait", return_value=127.4):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["retry_after_seconds"], 128)

    def test_non_throttle_exception_uses_default_handler(self):
        from unittest.mock import patch
        with patch("rest_framework.throttling.SimpleRateThrottle.allow_request", return_value=False), \
             patch("rest_framework.throttling.SimpleRateThrottle.wait", return_value=60.0):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertNotIn("detail", data)


# ---------------------------------------------------------------------------
# Serializer module structure
# ---------------------------------------------------------------------------

class SerializerModuleStructureTest(TestCase):
    """Verify per-app serializer modules exist and have expected classes."""

    def test_users_input_module_exists(self):
        mod = importlib.import_module("apps.users.serializers.input")
        self.assertTrue(hasattr(mod, "UserCreateSerializer"))

    def test_users_output_module_exists(self):
        mod = importlib.import_module("apps.users.serializers.output")
        self.assertTrue(hasattr(mod, "UserResponseSerializer"))
        self.assertTrue(hasattr(mod, "UserListSerializer"))

    def test_teams_input_module_exists(self):
        mod = importlib.import_module("apps.teams.serializers.input")
        self.assertTrue(hasattr(mod, "TeamCreateSerializer"))

    def test_teams_output_module_exists(self):
        mod = importlib.import_module("apps.teams.serializers.output")
        self.assertTrue(hasattr(mod, "TeamResponseSerializer"))
        self.assertTrue(hasattr(mod, "TeamListSerializer"))

    def test_tournaments_input_module_exists(self):
        mod = importlib.import_module("apps.tournaments.serializers.input")
        self.assertTrue(hasattr(mod, "TournamentCreateSerializer"))
        self.assertTrue(hasattr(mod, "MatchReportSerializer"))

    def test_tournaments_output_module_exists(self):
        mod = importlib.import_module("apps.tournaments.serializers.output")
        self.assertTrue(hasattr(mod, "TournamentResponseSerializer"))
        self.assertTrue(hasattr(mod, "TournamentListSerializer"))
        self.assertTrue(hasattr(mod, "MatchResponseSerializer"))
        self.assertTrue(hasattr(mod, "MatchListSerializer"))


# ---------------------------------------------------------------------------
# User serializer tests (from test_serializers.py)
# ---------------------------------------------------------------------------

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="secret", email="alice@test.com", role="player"
        )

    def test_contains_expected_fields(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        for field in ("id", "username", "role", "elo", "created_at"):
            self.assertIn(field, data)

    def test_password_not_in_output(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_email_in_output(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        self.assertIn("email", data)

    def test_avatar_url_in_output(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        self.assertIn("avatar_url", data)

    def test_all_required_api_fields_present(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        for field in ("id", "username", "email", "role", "elo", "avatar_url", "created_at"):
            self.assertIn(field, data, f"Missing field: {field}")

    def test_email_value_correct(self):
        from apps.users.serializers.output import UserResponseSerializer
        data = UserResponseSerializer(self.user).data
        self.assertEqual(data["email"], "alice@test.com")
