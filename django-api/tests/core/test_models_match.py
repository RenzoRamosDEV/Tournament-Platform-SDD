import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import EloHistory, Match, Team, Tournament, User


def make_user(username="u"):
    return User.objects.create_user(
        email=f"{username}@example.com", username=username, password="x", role="player"
    )


def make_team(name="T"):
    return Team.objects.create(name=name, owner=make_user(name + "_o"))


def make_tournament():
    return Tournament.objects.create(
        name="Cup",
        format="single_elimination",
        max_teams=8,
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 10),
        created_by=make_user("cup_creator"),
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
        self.assertEqual(m.status, "scheduled")
        self.assertIsNone(m.played_at)
        self.assertIsNone(m.winner_team)

    def test_invalid_status_raises_validation_error(self):
        m = Match(tournament=self.t, team_a=self.ta, team_b=self.tb, status="unknown")
        with self.assertRaises(ValidationError):
            m.full_clean()


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

    def test_null_winner_accepted_for_non_finished(self):
        m = Match.objects.create(tournament=self.t, team_a=self.ta, team_b=self.tb)
        self.assertIsNone(m.winner_team)


class MatchCleanTest(TestCase):
    def setUp(self):
        self.t = make_tournament()
        self.ta = make_team("A")
        self.tb = make_team("B")
        self.tc = make_team("C")

    def test_finished_without_winner_raises_validation_error(self):
        m = Match(tournament=self.t, team_a=self.ta, team_b=self.tb, status="finished")
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_finished_with_non_participant_winner_raises_validation_error(self):
        m = Match(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            status="finished", winner_team=self.tc,
        )
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_finished_with_team_a_as_winner_passes_clean(self):
        m = Match(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            status="finished", winner_team=self.ta,
        )
        m.full_clean()

    def test_finished_with_team_b_as_winner_passes_clean(self):
        m = Match(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            status="finished", winner_team=self.tb,
        )
        m.full_clean()

    def test_scheduled_without_winner_passes_clean(self):
        m = Match(tournament=self.t, team_a=self.ta, team_b=self.tb, status="scheduled")
        m.full_clean()


class EloHistoryTest(TestCase):
    def setUp(self):
        self.t = make_tournament()
        self.ta = make_team("A")
        self.tb = make_team("B")
        self.user = make_user("player")
        self.match = Match.objects.create(
            tournament=self.t, team_a=self.ta, team_b=self.tb,
            status="finished", winner_team=self.ta,
        )

    def test_elo_history_stores_fields(self):
        eh = EloHistory.objects.create(
            user=self.user, match=self.match, elo_before=1000, elo_after=1020
        )
        self.assertEqual(eh.elo_before, 1000)
        self.assertEqual(eh.elo_after, 1020)
        self.assertIsNotNone(eh.changed_at)

    def test_elo_history_deleted_when_user_deleted(self):
        EloHistory.objects.create(
            user=self.user, match=self.match, elo_before=1000, elo_after=1020
        )
        user_id = self.user.pk
        # Can't delete user because team_a owner has a team — use a separate user with no team
        standalone = make_user("standalone")
        eh = EloHistory.objects.create(
            user=standalone, match=self.match, elo_before=1000, elo_after=980
        )
        standalone_id = standalone.pk
        standalone.delete()
        self.assertFalse(EloHistory.objects.filter(user_id=standalone_id).exists())
