import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.teams.models import EloHistory, Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import User


_counter = 0


def _uid():
    global _counter
    _counter += 1
    return _counter


def make_user(role="player"):
    n = _uid()
    return User.objects.create_user(
        username=f"u{n}", email=f"u{n}@test.com", password="x", role=role
    )


def make_team(elo=1000):
    owner = make_user()
    t = Team.objects.create(name=f"Team{_uid()}", owner=owner)
    if elo != 1000:
        t.elo = elo
        t.save(update_fields=["elo"])
    return t


def make_tournament():
    admin = make_user(role="admin")
    return Tournament.objects.create(
        name=f"Cup{_uid()}",
        format="round_robin",
        max_teams=8,
        start_date=datetime.date(2026, 6, 1),
        end_date=datetime.date(2026, 6, 30),
        status="open",
        created_by=admin,
    )


def make_match(team_a, team_b, tournament=None):
    t = tournament or make_tournament()
    return Match.objects.create(tournament=t, team_a=team_a, team_b=team_b)


# ---------------------------------------------------------------------------
# GET /api/rankings/
# ---------------------------------------------------------------------------

class GlobalRankingListTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_returns_200(self):
        response = self.client.get("/api/rankings/")
        self.assertEqual(response.status_code, 200)

    def test_teams_ordered_by_elo_descending(self):
        t1 = make_team(elo=1200)
        t2 = make_team(elo=1000)
        t3 = make_team(elo=1100)
        response = self.client.get("/api/rankings/")
        ids = [r["id"] for r in response.data["results"]]
        self.assertEqual(ids, [t1.pk, t3.pk, t2.pk])

    def test_paginated_at_20(self):
        for _ in range(25):
            make_team()
        response = self.client.get("/api/rankings/")
        self.assertEqual(len(response.data["results"]), 20)

    def test_response_includes_pagination_metadata(self):
        for _ in range(25):
            make_team()
        response = self.client.get("/api/rankings/")
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

    def test_count_equals_total_teams(self):
        for _ in range(5):
            make_team()
        response = self.client.get("/api/rankings/")
        self.assertEqual(response.data["count"], 5)

    def test_result_includes_required_fields(self):
        make_team(elo=1050)
        response = self.client.get("/api/rankings/")
        r = response.data["results"][0]
        self.assertIn("id", r)
        self.assertIn("name", r)
        self.assertIn("elo", r)

    def test_empty_list_when_no_teams(self):
        response = self.client.get("/api/rankings/")
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])


# ---------------------------------------------------------------------------
# GET /api/rankings/?tournament_id=X
# ---------------------------------------------------------------------------

class TournamentRankingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tournament = make_tournament()

        self.t1 = make_team()
        self.t2 = make_team()
        self.t3 = make_team()

        m1 = make_match(self.t1, self.t2, tournament=self.tournament)
        m2 = make_match(self.t2, self.t3, tournament=self.tournament)

        EloHistory.objects.create(team=self.t1, match=m1, elo_before=1000, elo_after=1024)
        EloHistory.objects.create(team=self.t2, match=m1, elo_before=1000, elo_after=984)
        EloHistory.objects.create(team=self.t2, match=m2, elo_before=984, elo_after=1000)
        EloHistory.objects.create(team=self.t3, match=m2, elo_before=1000, elo_after=984)

    def test_ordered_by_elo_delta_descending(self):
        response = self.client.get(f"/api/rankings/?tournament_id={self.tournament.pk}")
        self.assertEqual(response.status_code, 200)
        ids = [r["id"] for r in response.data["results"]]
        # t1: +24, t2: -16+16=0, t3: -16
        self.assertEqual(ids[0], self.t1.pk)
        self.assertEqual(ids[-1], self.t3.pk)

    def test_excludes_teams_not_in_tournament(self):
        outsider = make_team()
        response = self.client.get(f"/api/rankings/?tournament_id={self.tournament.pk}")
        ids = [r["id"] for r in response.data["results"]]
        self.assertNotIn(outsider.pk, ids)

    def test_empty_for_unknown_tournament(self):
        response = self.client.get("/api/rankings/?tournament_id=99999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_result_includes_elo_delta(self):
        response = self.client.get(f"/api/rankings/?tournament_id={self.tournament.pk}")
        r = response.data["results"][0]
        self.assertIn("elo_delta", r)
        self.assertEqual(r["elo_delta"], 24)


# ---------------------------------------------------------------------------
# GET /api/teams/{id}/elo-history/
# ---------------------------------------------------------------------------

class EloHistoryEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.team = make_team()
        t = make_tournament()
        m1 = make_match(self.team, make_team(), tournament=t)
        m2 = make_match(self.team, make_team(), tournament=t)
        self.h1 = EloHistory.objects.create(team=self.team, match=m1, elo_before=1000, elo_after=1024)
        self.h2 = EloHistory.objects.create(team=self.team, match=m2, elo_before=1024, elo_after=1008)

    def test_returns_200(self):
        response = self.client.get(f"/api/teams/{self.team.pk}/elo-history/")
        self.assertEqual(response.status_code, 200)

    def test_returns_history_for_correct_team(self):
        response = self.client.get(f"/api/teams/{self.team.pk}/elo-history/")
        self.assertEqual(len(response.data), 2)

    def test_ordered_by_created_at_descending(self):
        response = self.client.get(f"/api/teams/{self.team.pk}/elo-history/")
        ids = [r["id"] for r in response.data]
        self.assertEqual(ids[0], self.h2.pk)
        self.assertEqual(ids[1], self.h1.pk)

    def test_result_includes_required_fields(self):
        response = self.client.get(f"/api/teams/{self.team.pk}/elo-history/")
        r = response.data[0]
        self.assertIn("elo_before", r)
        self.assertIn("elo_after", r)
        self.assertIn("match_id", r)
        self.assertIn("created_at", r)

    def test_404_for_unknown_team(self):
        response = self.client.get("/api/teams/99999/elo-history/")
        self.assertEqual(response.status_code, 404)

    def test_empty_list_for_team_with_no_history(self):
        new_team = make_team()
        response = self.client.get(f"/api/teams/{new_team.pk}/elo-history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
