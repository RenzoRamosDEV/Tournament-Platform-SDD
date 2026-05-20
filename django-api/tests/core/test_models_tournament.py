import datetime

from django.db import IntegrityError
from django.test import TestCase

from core.models import Team, Tournament, TournamentTeam, User


def make_user(username="u"):
    return User.objects.create_user(
        email=f"{username}@example.com", username=username, password="x", role="player"
    )


def make_team(name="T", owner=None):
    if owner is None:
        owner = make_user(name + "_owner")
    return Team.objects.create(name=name, owner=owner)


def make_tournament(creator=None, **kwargs):
    if creator is None:
        creator = make_user("creator")
    defaults = dict(
        name="Open Cup",
        format="single_elimination",
        max_teams=8,
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 10),
        created_by=creator,
    )
    defaults.update(kwargs)
    return Tournament.objects.create(**defaults)


class TournamentDefaultsTest(TestCase):
    def test_status_defaults_to_draft(self):
        t = make_tournament()
        self.assertEqual(t.status, "draft")

    def test_valid_statuses_accepted(self):
        creator = make_user("c")
        for s in ("draft", "open", "ongoing", "finished"):
            t = make_tournament(creator=creator, name=f"T_{s}", status=s)
            self.assertEqual(t.status, s)
            t.delete()

    def test_invalid_status_raises(self):
        with self.assertRaises(Exception):
            t = make_tournament(status="unknown")
            from django.db import connection
            connection.check_constraints()

    def test_format_single_elimination_accepted(self):
        t = make_tournament(format="single_elimination")
        self.assertEqual(t.format, "single_elimination")

    def test_format_round_robin_accepted(self):
        t = make_tournament(format="round_robin")
        self.assertEqual(t.format, "round_robin")

    def test_invalid_format_raises(self):
        with self.assertRaises(Exception):
            t = make_tournament(format="bracket")
            from django.db import connection
            connection.check_constraints()

    def test_max_teams_zero_raises(self):
        with self.assertRaises(Exception):
            t = make_tournament(max_teams=0)
            from django.db import connection
            connection.check_constraints()

    def test_end_date_before_start_date_raises(self):
        with self.assertRaises(Exception):
            t = make_tournament(
                start_date=datetime.date(2026, 1, 10),
                end_date=datetime.date(2026, 1, 1),
            )
            from django.db import connection
            connection.check_constraints()

    def test_created_by_is_stored(self):
        creator = make_user("org")
        t = make_tournament(creator=creator)
        self.assertEqual(t.created_by, creator)


class TournamentTeamTest(TestCase):
    def setUp(self):
        self.tournament = make_tournament()
        self.team = make_team()

    def test_registration_sets_registered_at(self):
        tt = TournamentTeam.objects.create(tournament=self.tournament, team=self.team)
        self.assertIsNotNone(tt.registered_at)

    def test_duplicate_registration_rejected(self):
        TournamentTeam.objects.create(tournament=self.tournament, team=self.team)
        with self.assertRaises(IntegrityError):
            TournamentTeam.objects.create(tournament=self.tournament, team=self.team)
