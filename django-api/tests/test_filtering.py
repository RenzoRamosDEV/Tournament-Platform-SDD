import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.teams.models import Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import User


def make_admin(suffix=""):
    return User.objects.create_user(
        username=f"filter_admin{suffix}", email=f"filter_admin{suffix}@test.com",
        password="x", role="admin",
    )


def make_tournament(admin, name, status="open", start_date=None, end_date=None):
    return Tournament.objects.create(
        name=name, format="round_robin", max_teams=8,
        status=status,
        start_date=start_date or datetime.date(2026, 6, 1),
        end_date=end_date or datetime.date(2026, 6, 30),
        created_by=admin,
    )


def make_team(n, owner):
    return Team.objects.create(name=f"FTeam{n}", owner=owner)


def make_match(tournament, team_a, team_b, played_at=None):
    m = Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b)
    if played_at:
        Match.objects.filter(pk=m.pk).update(
            played_at=played_at, status="finished",
            winner_team_id=team_a.id, score_a=1, score_b=0,
        )
        m.refresh_from_db()
    return m


class TournamentDateFilterTest(TestCase):
    def setUp(self):
        self.admin = make_admin("_t")
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.t_june = make_tournament(
            self.admin, "JuneCup",
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
        )
        self.t_july = make_tournament(
            self.admin, "JulyCup",
            start_date=datetime.date(2026, 7, 1),
            end_date=datetime.date(2026, 7, 31),
        )

    def test_date_from_filters_tournaments(self):
        response = self.client.get("/api/tournaments/?date_from=2026-07-01")
        self.assertEqual(response.status_code, 200)
        names = [t["name"] for t in response.json()["results"]]
        self.assertIn("JulyCup", names)
        self.assertNotIn("JuneCup", names)

    def test_date_to_filters_tournaments(self):
        response = self.client.get("/api/tournaments/?date_to=2026-06-30")
        self.assertEqual(response.status_code, 200)
        names = [t["name"] for t in response.json()["results"]]
        self.assertIn("JuneCup", names)
        self.assertNotIn("JulyCup", names)

    def test_invalid_date_format_returns_400(self):
        response = self.client.get("/api/tournaments/?date_from=not-a-date")
        self.assertEqual(response.status_code, 400)

    def test_created_by_filter_returns_matching_tournaments(self):
        other_admin = make_admin("_other")
        make_tournament(other_admin, "OtherCup")
        response = self.client.get(f"/api/tournaments/?created_by={self.admin.id}")
        self.assertEqual(response.status_code, 200)
        names = [t["name"] for t in response.json()["results"]]
        self.assertIn("JuneCup", names)
        self.assertNotIn("OtherCup", names)

    def test_created_by_nonexistent_user_returns_empty(self):
        response = self.client.get("/api/tournaments/?created_by=99999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])


class MatchDateFilterTest(TestCase):
    def setUp(self):
        self.admin = make_admin("_m")
        self.client = APIClient()
        self.ta = make_team("a", self.admin)
        self.tb = make_team("b", self.admin)
        self.t = make_tournament(self.admin, "MCup")

        self.m_june = make_match(
            self.t, self.ta, self.tb,
            played_at=datetime.datetime(2026, 6, 15),
        )
        self.m_july = make_match(
            self.t, self.ta, self.tb,
            played_at=datetime.datetime(2026, 7, 15),
        )

    def test_date_from_filters_matches(self):
        response = self.client.get("/api/matches/?date_from=2026-07-01")
        self.assertEqual(response.status_code, 200)
        ids = [m["id"] for m in response.json()["results"]]
        self.assertIn(self.m_july.id, ids)
        self.assertNotIn(self.m_june.id, ids)

    def test_date_to_filters_matches(self):
        response = self.client.get("/api/matches/?date_to=2026-06-30")
        self.assertEqual(response.status_code, 200)
        ids = [m["id"] for m in response.json()["results"]]
        self.assertIn(self.m_june.id, ids)
        self.assertNotIn(self.m_july.id, ids)

    def test_invalid_date_format_returns_400(self):
        response = self.client.get("/api/matches/?date_from=bad-date")
        self.assertEqual(response.status_code, 400)
