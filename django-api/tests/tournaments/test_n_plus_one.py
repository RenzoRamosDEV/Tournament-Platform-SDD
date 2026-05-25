import datetime

from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIClient

from apps.teams.models import Team
from apps.tournaments.models import Match, Tournament, TournamentTeam
from apps.users.models import User


def make_user(n):
    return User.objects.create_user(
        username=f"u{n}", email=f"u{n}@test.com", password="x", role="admin"
    )


def make_team(n, owner):
    return Team.objects.create(name=f"T{n}", owner=owner)


def make_tournament(n, admin):
    return Tournament.objects.create(
        name=f"Cup{n}", format="round_robin", max_teams=8,
        start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2026, 1, 31),
        status="open", created_by=admin,
    )


def make_match(n, tournament, team_a, team_b):
    return Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b)


class TournamentListNPlusOneTest(TestCase):
    def test_tournament_list_query_count_constant(self):
        admin = make_user(1)
        teams = [make_team(i, admin) for i in range(3)]
        for i in range(2):
            t = make_tournament(i, admin)
            for team in teams:
                TournamentTeam.objects.create(tournament=t, team=team)

        client = APIClient()
        client.force_authenticate(user=admin)

        with CaptureQueriesContext(connection) as ctx_small:
            client.get("/api/tournaments/")
        count_small = len(ctx_small)

        for i in range(2, 8):
            t = make_tournament(i, admin)
            for team in teams:
                TournamentTeam.objects.create(tournament=t, team=team)

        with CaptureQueriesContext(connection) as ctx_large:
            client.get("/api/tournaments/")
        count_large = len(ctx_large)

        self.assertEqual(count_small, count_large, (
            f"Query count changed from {count_small} to {count_large} as dataset grew — N+1 detected"
        ))


class MatchListNPlusOneTest(TestCase):
    def test_match_list_query_count_constant(self):
        admin = make_user(2)
        ta = make_team("A", admin)
        tb = make_team("B", admin)
        t = make_tournament("X", admin)
        for i in range(3):
            make_match(i, t, ta, tb)

        client = APIClient()

        with CaptureQueriesContext(connection) as ctx_small:
            client.get("/api/matches/")
        count_small = len(ctx_small)

        for i in range(3, 10):
            make_match(i, t, ta, tb)

        with CaptureQueriesContext(connection) as ctx_large:
            client.get("/api/matches/")
        count_large = len(ctx_large)

        self.assertEqual(count_small, count_large, (
            f"Query count changed from {count_small} to {count_large} as dataset grew — N+1 detected"
        ))


class TeamListNPlusOneTest(TestCase):
    def test_team_list_query_count_constant(self):
        admin = make_user(3)
        teams = [make_team(i, admin) for i in range(3)]
        t = make_tournament("Z", admin)
        for team in teams:
            TournamentTeam.objects.create(tournament=t, team=team)

        client = APIClient()

        with CaptureQueriesContext(connection) as ctx_small:
            client.get("/api/teams/")
        count_small = len(ctx_small)

        more_teams = [make_team(f"x{i}", admin) for i in range(5)]
        for team in more_teams:
            TournamentTeam.objects.create(tournament=t, team=team)

        with CaptureQueriesContext(connection) as ctx_large:
            client.get("/api/teams/")
        count_large = len(ctx_large)

        self.assertEqual(count_small, count_large, (
            f"Query count changed from {count_small} to {count_large} as dataset grew — N+1 detected"
        ))
