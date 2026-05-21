import datetime

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.teams.models import Team, TeamMember
from apps.tournaments.models import Tournament, TournamentTeam
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
# Team List API
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
# Team serializer tests (from test_serializers.py)
# ---------------------------------------------------------------------------

class TeamSerializerTest(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.team = Team.objects.create(name="Alpha", owner=self.owner)

    def test_contains_expected_fields(self):
        from apps.teams.serializers.output import TeamResponseSerializer
        data = TeamResponseSerializer(self.team).data
        for field in ("id", "name", "owner", "created_at"):
            self.assertIn(field, data)


class TeamMemberSerializerTest(TestCase):
    def setUp(self):
        owner = make_user()
        member = make_user()
        team = Team.objects.create(name="T1", owner=owner)
        self.tm = TeamMember.objects.create(user=member, team=team)

    def test_contains_expected_fields(self):
        from apps.teams.serializers.output import TeamMemberSerializer
        data = TeamMemberSerializer(self.tm).data
        for field in ("user", "team", "joined_at"):
            self.assertIn(field, data)


class TeamSerializerOwnerReadOnlyTest(TestCase):
    def setUp(self):
        self.owner = make_user()

    def test_owner_is_read_only(self):
        from apps.teams.serializers.output import TeamResponseSerializer
        s = TeamResponseSerializer(data={"name": "Beta", "owner": self.owner.id})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn("owner", s.validated_data)

    def test_owner_present_in_serialized_output(self):
        from apps.teams.serializers.output import TeamResponseSerializer
        team = Team.objects.create(name="Gamma", owner=self.owner)
        data = TeamResponseSerializer(team).data
        self.assertIn("owner", data)
        self.assertEqual(data["owner"], self.owner.id)
