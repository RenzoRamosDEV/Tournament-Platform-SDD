import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Match, Team, Tournament, TournamentTeam, User


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


def make_match(tournament=None, team_a=None, team_b=None):
    if tournament is None:
        tournament = make_tournament()
    if team_a is None:
        team_a = make_team()
    if team_b is None:
        team_b = make_team()
    return Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b)


def auth_client(user):
    """Return an APIClient force-authenticated as user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Existing registration smoke test (updated)
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
# 3. User List API
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
# 4. Team API
# ---------------------------------------------------------------------------

class TeamListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("team-list")
        make_team()

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
        item = response.json()["results"][0]
        for field in ("id", "name", "owner", "created_at"):
            self.assertIn(field, item)


class TeamListFilterTest(TestCase):
    def setUp(self):
        self.url = reverse("team-list")
        self.admin = make_user(role="admin")
        self.t1 = make_tournament(created_by=self.admin)
        self.t2 = make_tournament(created_by=self.admin)
        self.team_in = make_team()
        self.team_out = make_team()
        TournamentTeam.objects.create(tournament=self.t1, team=self.team_in)

    def test_filter_by_tournament_returns_only_registered_teams(self):
        response = self.client.get(self.url, {"tournament_id": self.t1.id})
        self.assertEqual(response.status_code, 200)
        ids = [t["id"] for t in response.json()["results"]]
        self.assertIn(self.team_in.id, ids)
        self.assertNotIn(self.team_out.id, ids)

    def test_filter_by_nonexistent_tournament_returns_empty(self):
        response = self.client.get(self.url, {"tournament_id": 99999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])


class TeamCreateViewTest(TestCase):
    def setUp(self):
        self.url = reverse("team-list")
        self.player = make_user(role="player")

    def test_authenticated_create_returns_201(self):
        client = auth_client(self.player)
        response = client.post(self.url, {"name": "New Team"}, format="json")
        self.assertEqual(response.status_code, 201)

    def test_owner_set_to_request_user(self):
        client = auth_client(self.player)
        response = client.post(self.url, {"name": "Owned Team"}, format="json")
        self.assertEqual(response.json()["owner"], self.player.id)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(self.url, {"name": "Anon Team"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_missing_name_returns_400(self):
        client = auth_client(self.player)
        response = client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    def test_duplicate_name_returns_400(self):
        make_team(name="Duplicate", owner=self.player)
        client = auth_client(self.player)
        response = client.post(self.url, {"name": "Duplicate"}, format="json")
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# 5. Tournament API
# ---------------------------------------------------------------------------

class TournamentListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("tournament-list")
        self.admin = make_user(role="admin")
        self.organizer = make_user(role="organizer")
        self.player = make_user(role="player")
        self.t_open = make_tournament(status="open")
        self.t_draft = make_tournament(status="draft")
        self.t_finished = make_tournament(status="finished")

    def test_public_access_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_draft_excluded_for_anonymous(self):
        response = self.client.get(self.url)
        statuses = [t["status"] for t in response.json()["results"]]
        self.assertNotIn("draft", statuses)

    def test_draft_excluded_for_player(self):
        client = auth_client(self.player)
        response = client.get(self.url)
        statuses = [t["status"] for t in response.json()["results"]]
        self.assertNotIn("draft", statuses)

    def test_draft_visible_for_admin(self):
        client = auth_client(self.admin)
        response = client.get(self.url)
        statuses = [t["status"] for t in response.json()["results"]]
        self.assertIn("draft", statuses)

    def test_draft_visible_for_organizer(self):
        client = auth_client(self.organizer)
        response = client.get(self.url)
        statuses = [t["status"] for t in response.json()["results"]]
        self.assertIn("draft", statuses)

    def test_filter_by_valid_status(self):
        response = self.client.get(self.url, {"status": "open"})
        self.assertEqual(response.status_code, 200)
        for t in response.json()["results"]:
            self.assertEqual(t["status"], "open")

    def test_filter_by_invalid_status_returns_400(self):
        response = self.client.get(self.url, {"status": "invalid"})
        self.assertEqual(response.status_code, 400)


class TournamentCreateViewTest(TestCase):
    def setUp(self):
        self.url = reverse("tournament-list")
        self.admin = make_user(role="admin")
        self.player = make_user(role="player")
        self.valid_data = {
            "name": "Spring Cup",
            "format": "single_elimination",
            "max_teams": 16,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        }

    def test_admin_create_returns_201(self):
        client = auth_client(self.admin)
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_created_by_set_to_admin(self):
        client = auth_client(self.admin)
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.json()["created_by"], self.admin.id)

    def test_initial_status_is_draft(self):
        client = auth_client(self.admin)
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.json()["status"], "draft")

    def test_non_admin_returns_403(self):
        client = auth_client(self.player)
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(self.url, self.valid_data, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_end_date_before_start_date_returns_400(self):
        client = auth_client(self.admin)
        data = {**self.valid_data, "start_date": "2026-06-30", "end_date": "2026-06-01"}
        response = client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.json())


# ---------------------------------------------------------------------------
# 6. Match API
# ---------------------------------------------------------------------------

class MatchListViewTest(TestCase):
    def setUp(self):
        self.url = reverse("match-list")
        self.t1 = make_tournament()
        self.t2 = make_tournament()
        make_match(tournament=self.t1)
        make_match(tournament=self.t2)

    def test_public_access_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_pagination_envelope_present(self):
        response = self.client.get(self.url)
        data = response.json()
        for key in ("next", "previous", "results"):
            self.assertIn(key, data)

    def test_filter_by_tournament_id(self):
        response = self.client.get(self.url, {"tournament_id": self.t1.id})
        self.assertEqual(response.status_code, 200)
        for m in response.json()["results"]:
            self.assertEqual(m["tournament"], self.t1.id)

    def test_filter_nonexistent_tournament_returns_empty(self):
        response = self.client.get(self.url, {"tournament_id": 99999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_cursor_pagination_has_no_count_key(self):
        response = self.client.get(self.url)
        data = response.json()
        self.assertNotIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertIn("results", data)

    def test_filter_by_valid_status(self):
        t = make_tournament()
        response = self.client.get(self.url, {"status": "scheduled"})
        self.assertEqual(response.status_code, 200)
        for m in response.json()["results"]:
            self.assertEqual(m["status"], "scheduled")

    def test_filter_by_invalid_status_returns_400(self):
        response = self.client.get(self.url, {"status": "postponed"})
        self.assertEqual(response.status_code, 400)

    def test_cursor_pagination_consistent_under_inserts(self):
        t = make_tournament()
        for _ in range(5):
            make_match(tournament=t)
        r1 = self.client.get(self.url, {"page_size": 3})
        self.assertEqual(r1.status_code, 200)
        page1_ids = {m["id"] for m in r1.json()["results"]}
        next_url = r1.json().get("next")
        if next_url:
            make_match(tournament=t)
            r2 = self.client.get(next_url)
            page2_ids = {m["id"] for m in r2.json()["results"]}
            self.assertEqual(len(page1_ids & page2_ids), 0)


class MatchReportViewTest(TestCase):
    def setUp(self):
        self.admin = make_user(role="admin")
        self.player = make_user(role="player")
        self.ta = make_team()
        self.tb = make_team()
        self.tournament = make_tournament()
        self.match = make_match(
            tournament=self.tournament, team_a=self.ta, team_b=self.tb
        )
        self.url = reverse("match-report", kwargs={"pk": self.match.id})
        self.valid_data = {
            "winner_id": self.ta.id,
            "score_team_a": 3,
            "score_team_b": 1,
        }

    def test_first_submission_returns_201(self):
        client = auth_client(self.player)
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_first_submission_sets_result_fields(self):
        client = auth_client(self.player)
        client.post(self.url, self.valid_data, format="json")
        self.match.refresh_from_db()
        self.assertEqual(self.match.winner_team_id, self.ta.id)
        self.assertEqual(self.match.score_a, 3)
        self.assertEqual(self.match.score_b, 1)
        self.assertEqual(self.match.status, "finished")
        self.assertIsNotNone(self.match.played_at)

    def test_non_admin_duplicate_returns_409(self):
        client = auth_client(self.player)
        client.post(self.url, self.valid_data, format="json")
        response = client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 409)

    def test_admin_overwrite_returns_200(self):
        auth_client(self.player).post(self.url, self.valid_data, format="json")
        new_data = {"winner_id": self.tb.id, "score_team_a": 0, "score_team_b": 2}
        response = auth_client(self.admin).post(self.url, new_data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_admin_overwrite_updates_result(self):
        auth_client(self.player).post(self.url, self.valid_data, format="json")
        new_data = {"winner_id": self.tb.id, "score_team_a": 0, "score_team_b": 2}
        auth_client(self.admin).post(self.url, new_data, format="json")
        self.match.refresh_from_db()
        self.assertEqual(self.match.winner_team_id, self.tb.id)

    def test_match_not_found_returns_404(self):
        url = reverse("match-report", kwargs={"pk": 99999})
        client = auth_client(self.player)
        response = client.post(url, self.valid_data, format="json")
        self.assertEqual(response.status_code, 404)

    def test_invalid_winner_id_returns_400(self):
        other = make_team()
        client = auth_client(self.player)
        response = client.post(
            self.url,
            {"winner_id": other.id, "score_team_a": 1, "score_team_b": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("winner_id", response.json())

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            self.url, self.valid_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# 7. Throttling & custom exception handler
# ---------------------------------------------------------------------------

class SerializerModuleStructureTest(TestCase):
    """Verify serializers.py no longer exists and input/output modules are present."""

    def test_core_serializers_module_does_not_exist(self):
        import importlib
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.serializers")

    def test_core_input_module_exists(self):
        import importlib
        mod = importlib.import_module("core.input")
        self.assertTrue(hasattr(mod, "UserCreateSerializer"))
        self.assertTrue(hasattr(mod, "TeamCreateSerializer"))
        self.assertTrue(hasattr(mod, "TournamentCreateSerializer"))
        self.assertTrue(hasattr(mod, "MatchReportSerializer"))

    def test_core_output_module_exists(self):
        import importlib
        mod = importlib.import_module("core.output")
        self.assertTrue(hasattr(mod, "UserResponseSerializer"))
        self.assertTrue(hasattr(mod, "UserListSerializer"))
        self.assertTrue(hasattr(mod, "TeamResponseSerializer"))
        self.assertTrue(hasattr(mod, "TeamListSerializer"))
        self.assertTrue(hasattr(mod, "TournamentResponseSerializer"))
        self.assertTrue(hasattr(mod, "TournamentListSerializer"))
        self.assertTrue(hasattr(mod, "MatchResponseSerializer"))
        self.assertTrue(hasattr(mod, "MatchListSerializer"))


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


class ThrottleExceptionHandlerTest(TestCase):
    """Custom 429 body and delegation of non-throttle exceptions."""

    def setUp(self):
        self.url = reverse("user-list")

    def _patch_throttle(self, wait_seconds):
        """Return a context manager that forces every throttle check to fail."""
        from unittest.mock import patch
        return patch(
            "rest_framework.throttling.SimpleRateThrottle.allow_request",
            return_value=False,
        ), patch(
            "rest_framework.throttling.SimpleRateThrottle.wait",
            return_value=wait_seconds,
        )

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
