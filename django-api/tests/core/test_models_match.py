import datetime

from django.db import IntegrityError
from django.test import TestCase

from core.models import Match, Team, Tournament, User


def make_user(username="u"):
    return User.objects.create_user(username=username, password="x", role="player")


def make_team(name="T"):
    return Team.objects.create(name=name, owner=make_user(name + "_o"))


def make_tournament():
    return Tournament.objects.create(
        name="Cup",
        format="single_elim",
        max_teams=8,
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 10),
    )


class MatchDefaultsTest(TestCase):
    def setUp(self):
        self.t = make_tournament()
        self.ta = make_team("A")
        self.tb = make_team("B")

    def test_defaults(self):
        m = Match.objects.create(tournament=self.t, team_a=self.ta, team_b=self.tb)
        self.assertEqual(m.score_a, 0)
        self.assertEqual(m.score_b, 0)
        self.assertEqual(m.status, "pending")
        self.assertIsNone(m.played_at)
        self.assertIsNone(m.winner_team)

    def test_invalid_status_raises(self):
        with self.assertRaises(Exception):
            Match.objects.create(
                tournament=self.t, team_a=self.ta, team_b=self.tb, status="unknown"
            )
            from django.db import connection
            connection.check_constraints()


class MatchWinnerConstraintTest(TestCase):
    def setUp(self):
        self.t = make_tournament()
        self.ta = make_team("A")
        self.tb = make_team("B")
        self.tc = make_team("C")

    def test_winner_team_a_accepted(self):
        m = Match.objects.create(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            winner_team=self.ta, status="finished",
        )
        self.assertEqual(m.winner_team, self.ta)

    def test_winner_team_b_accepted(self):
        m = Match.objects.create(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            winner_team=self.tb, status="finished",
        )
        self.assertEqual(m.winner_team, self.tb)

    def test_null_winner_accepted(self):
        m = Match.objects.create(tournament=self.t, team_a=self.ta, team_b=self.tb)
        self.assertIsNone(m.winner_team)

    def test_invalid_winner_rejected(self):
        with self.assertRaises(Exception):
            Match.objects.create(
                tournament=self.t, team_a=self.ta, team_b=self.tb,
                winner_team=self.tc, status="finished",
            )
            from django.db import connection
            connection.check_constraints()
