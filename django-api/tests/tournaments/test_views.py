import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.teams.models import Team
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


def make_match(tournament=None, team_a=None, team_b=None):
    if tournament is None:
        tournament = make_tournament()
    if team_a is None:
        team_a = make_team()
    if team_b is None:
        team_b = make_team()
    return Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b)


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Tournament List API
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
# Match List API
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
        make_tournament()
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
# Tournament serializer tests (from test_serializers.py)
# ---------------------------------------------------------------------------

class TournamentSerializerTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="org1", password="x", email="org1@x.com", role="organizer"
        )
        self.tournament = Tournament.objects.create(
            name="Cup",
            format="round_robin",
            max_teams=8,
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
            created_by=self.creator,
        )

    def test_contains_expected_fields(self):
        from apps.tournaments.serializers.output import TournamentResponseSerializer
        data = TournamentResponseSerializer(self.tournament).data
        for field in ("id", "name", "status", "format", "max_teams", "start_date", "end_date"):
            self.assertIn(field, data)

    def test_status_default_in_output(self):
        from apps.tournaments.serializers.output import TournamentResponseSerializer
        data = TournamentResponseSerializer(self.tournament).data
        self.assertEqual(data["status"], "draft")

    def test_created_by_in_output(self):
        from apps.tournaments.serializers.output import TournamentResponseSerializer
        data = TournamentResponseSerializer(self.tournament).data
        self.assertIn("created_by", data)

    def test_end_date_before_start_date_invalid(self):
        from apps.tournaments.serializers.output import TournamentResponseSerializer
        s = TournamentResponseSerializer(data={
            "name": "Bad Cup",
            "format": "round_robin",
            "max_teams": 8,
            "start_date": "2026-06-30",
            "end_date": "2026-06-01",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_end_date_equal_start_date_valid(self):
        from apps.tournaments.serializers.output import TournamentResponseSerializer
        s = TournamentResponseSerializer(data={
            "name": "One Day Cup",
            "format": "round_robin",
            "max_teams": 4,
            "start_date": "2026-06-15",
            "end_date": "2026-06-15",
        })
        self.assertTrue(s.is_valid(), s.errors)


class TournamentTeamSerializerTest(TestCase):
    def setUp(self):
        creator = make_user(role="organizer")
        t = Tournament.objects.create(
            name="Cup",
            format="round_robin",
            max_teams=4,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 10),
            created_by=creator,
        )
        team = make_team()
        self.tt = TournamentTeam.objects.create(tournament=t, team=team)

    def test_contains_expected_fields(self):
        from apps.tournaments.serializers.output import TournamentTeamSerializer
        data = TournamentTeamSerializer(self.tt).data
        for field in ("tournament", "team", "registered_at"):
            self.assertIn(field, data)


class MatchSerializerTest(TestCase):
    def setUp(self):
        creator = make_user(role="organizer")
        self.tournament = Tournament.objects.create(
            name="Cup",
            format="round_robin",
            max_teams=4,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 10),
            created_by=creator,
        )
        self.ta = make_team()
        self.tb = make_team()
        self.tc = make_team()

    def test_contains_expected_fields(self):
        from apps.tournaments.serializers.output import MatchResponseSerializer
        m = Match.objects.create(tournament=self.tournament, team_a=self.ta, team_b=self.tb)
        data = MatchResponseSerializer(m).data
        for field in ("id", "tournament", "team_a", "team_b", "winner_team", "score_a", "score_b", "status", "played_at"):
            self.assertIn(field, data)

    def test_invalid_winner_raises_validation_error(self):
        from apps.tournaments.serializers.output import MatchResponseSerializer
        s = MatchResponseSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.tc.id,
            "status": "finished",
            "score_a": 1,
            "score_b": 0,
        })
        self.assertFalse(s.is_valid())
        self.assertIn("winner_team", s.errors)

    def test_valid_winner_passes_validation(self):
        from apps.tournaments.serializers.output import MatchResponseSerializer
        s = MatchResponseSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.ta.id,
            "status": "finished",
            "score_a": 1,
            "score_b": 0,
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_null_winner_passes_validation(self):
        from apps.tournaments.serializers.output import MatchResponseSerializer
        s = MatchResponseSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "status": "scheduled",
            "score_a": 0,
            "score_b": 0,
        })
        self.assertTrue(s.is_valid(), s.errors)


class MatchReportSerializerTest(TestCase):
    def setUp(self):
        creator = make_user(role="organizer")
        self.ta = make_team()
        self.tb = make_team()
        self.tournament = Tournament.objects.create(
            name="RC",
            format="round_robin",
            max_teams=4,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 10),
            created_by=creator,
        )
        self.match = Match.objects.create(
            tournament=self.tournament,
            team_a=self.ta,
            team_b=self.tb,
        )

    def test_valid_winner_team_a(self):
        from apps.tournaments.serializers.input import MatchReportSerializer
        s = MatchReportSerializer(
            data={"winner_id": self.ta.id, "score_team_a": 3, "score_team_b": 1},
            context={"match": self.match},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_winner_team_b(self):
        from apps.tournaments.serializers.input import MatchReportSerializer
        s = MatchReportSerializer(
            data={"winner_id": self.tb.id, "score_team_a": 0, "score_team_b": 2},
            context={"match": self.match},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_winner_not_in_match(self):
        from apps.tournaments.serializers.input import MatchReportSerializer
        other = make_team()
        s = MatchReportSerializer(
            data={"winner_id": other.id, "score_team_a": 1, "score_team_b": 0},
            context={"match": self.match},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("winner_id", s.errors)

    def test_negative_score_invalid(self):
        from apps.tournaments.serializers.input import MatchReportSerializer
        s = MatchReportSerializer(
            data={"winner_id": self.ta.id, "score_team_a": -1, "score_team_b": 0},
            context={"match": self.match},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("score_team_a", s.errors)
