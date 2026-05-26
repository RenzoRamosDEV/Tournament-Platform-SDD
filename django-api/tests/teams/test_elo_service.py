import datetime

from django.db import transaction
from django.test import TestCase

from apps.teams.models import EloHistory, Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import User


def make_user(username, role="player"):
    return User.objects.create_user(
        email=f"{username}@example.com", username=username, password="x", role=role
    )


def make_team(name, elo=1000):
    owner = make_user(f"owner_{name}")
    t = Team.objects.create(name=name, owner=owner)
    if elo != 1000:
        t.elo = elo
        t.save(update_fields=["elo"])
    return t


def make_tournament():
    admin = make_user("t_admin_elo")
    return Tournament.objects.create(
        name="EloTestCup",
        format="round_robin",
        max_teams=4,
        start_date=datetime.date(2026, 6, 1),
        end_date=datetime.date(2026, 6, 30),
        status="open",
        created_by=admin,
    )


def make_match(team_a, team_b, tournament=None):
    t = tournament or make_tournament()
    return Match.objects.create(tournament=t, team_a=team_a, team_b=team_b)


# ---------------------------------------------------------------------------
# calculate_elo
# ---------------------------------------------------------------------------

class CalculateEloTest(TestCase):
    def setUp(self):
        from apps.teams.services import calculate_elo
        self.calculate_elo = calculate_elo

    def test_equal_elos_symmetric_exchange(self):
        w, l = self.calculate_elo(1000, 1000)
        self.assertEqual(w, 1016)
        self.assertEqual(l, 984)

    def test_favorite_wins_fewer_points(self):
        w, l = self.calculate_elo(1200, 1000)
        self.assertLess(w - 1200, 16)
        self.assertGreater(w, 1200)
        self.assertLess(l, 1000)

    def test_underdog_wins_more_points(self):
        w, l = self.calculate_elo(1000, 1200)
        self.assertGreater(w - 1000, 16)
        self.assertGreater(w, 1000)
        self.assertLess(l, 1200)

    def test_custom_k_factor(self):
        w, l = self.calculate_elo(1000, 1000, k=16)
        self.assertEqual(w, 1008)
        self.assertEqual(l, 992)

    def test_returns_integers(self):
        w, l = self.calculate_elo(1000, 1000)
        self.assertIsInstance(w, int)
        self.assertIsInstance(l, int)

    def test_sum_of_changes_is_zero(self):
        """ELO is zero-sum: what one gains the other loses."""
        w, l = self.calculate_elo(1100, 950)
        self.assertEqual((w - 1100) + (l - 950), 0)

    def test_underdog_exact_values(self):
        """Exact values for underdog winning — catches k mutations (k=32 gives 1024, k=33 gives 1025)."""
        w, l = self.calculate_elo(1000, 1200)
        self.assertEqual(w, 1024)
        self.assertEqual(l, 1176)

    def test_favorite_exact_values(self):
        """Exact values for favorite winning — catches k mutations."""
        w, l = self.calculate_elo(1200, 1000)
        self.assertEqual(w, 1208)
        self.assertEqual(l, 992)


# ---------------------------------------------------------------------------
# update_elo
# ---------------------------------------------------------------------------

class UpdateEloTest(TestCase):
    def setUp(self):
        from apps.teams.services import update_elo
        self.update_elo = update_elo
        self.ta = make_team("WinnerTeam", elo=1200)
        self.tb = make_team("LoserTeam", elo=1000)
        self.match = make_match(self.ta, self.tb)
        self.match.winner_team = self.ta
        self.match.status = "finished"
        self.match.save()

    def test_elo_updated_and_history_created(self):
        self.update_elo(self.match)

        self.ta.refresh_from_db()
        self.tb.refresh_from_db()

        self.assertGreater(self.ta.elo, 1200)
        self.assertLess(self.tb.elo, 1000)
        self.assertEqual(EloHistory.objects.filter(match=self.match).count(), 2)

    def test_winner_history_correct(self):
        self.update_elo(self.match)
        h = EloHistory.objects.get(team=self.ta, match=self.match)
        self.assertEqual(h.elo_before, 1200)
        self.assertGreater(h.elo_after, 1200)

    def test_loser_history_correct(self):
        self.update_elo(self.match)
        h = EloHistory.objects.get(team=self.tb, match=self.match)
        self.assertEqual(h.elo_before, 1000)
        self.assertLess(h.elo_after, 1000)

    def test_idempotent_on_duplicate_call(self):
        self.update_elo(self.match)
        self.ta.refresh_from_db()
        elo_after_first = self.ta.elo

        self.update_elo(self.match)
        self.ta.refresh_from_db()

        self.assertEqual(self.ta.elo, elo_after_first)
        self.assertEqual(EloHistory.objects.filter(match=self.match).count(), 2)

    def test_no_exception_on_idempotent_call(self):
        self.update_elo(self.match)
        try:
            self.update_elo(self.match)
        except Exception as e:
            self.fail(f"update_elo raised unexpectedly on duplicate call: {e}")
