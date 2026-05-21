from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.teams.models import Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import EloHistory, User


class SeedDataEntityCountsTest(TestCase):
    def test_creates_20_users(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(User.objects.count(), 20)

    def test_creates_1_admin(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(User.objects.filter(role="admin").count(), 1)

    def test_creates_3_organizers(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(User.objects.filter(role="organizer").count(), 3)

    def test_creates_16_players(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(User.objects.filter(role="player").count(), 16)

    def test_creates_6_teams(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Team.objects.count(), 6)

    def test_creates_3_tournaments(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Tournament.objects.count(), 3)

    def test_creates_one_finished_tournament(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Tournament.objects.filter(status="finished").count(), 1)

    def test_creates_one_ongoing_tournament(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Tournament.objects.filter(status="ongoing").count(), 1)

    def test_creates_one_open_tournament(self):
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Tournament.objects.filter(status="open").count(), 1)

    def test_all_users_start_with_elo_1000(self):
        call_command("seed_data", stdout=StringIO())
        self.assertTrue(User.objects.filter(elo=1000).count() == 20)

    def test_finished_matches_have_elo_history(self):
        call_command("seed_data", stdout=StringIO())
        finished_matches = Match.objects.filter(status="finished")
        self.assertGreater(finished_matches.count(), 0)
        for match in finished_matches:
            self.assertGreater(
                EloHistory.objects.filter(match=match).count(), 0,
                f"Match {match.pk} has no EloHistory records",
            )


class SeedDataIdempotencyTest(TestCase):
    def test_second_run_does_not_duplicate_users(self):
        call_command("seed_data", stdout=StringIO())
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(User.objects.count(), 20)

    def test_second_run_does_not_duplicate_teams(self):
        call_command("seed_data", stdout=StringIO())
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Team.objects.count(), 6)

    def test_second_run_does_not_duplicate_tournaments(self):
        call_command("seed_data", stdout=StringIO())
        call_command("seed_data", stdout=StringIO())
        self.assertEqual(Tournament.objects.count(), 3)


class SeedDataClearFlagTest(TestCase):
    @override_settings(DEBUG=False)
    def test_clear_blocked_when_debug_false(self):
        call_command("seed_data", stdout=StringIO())
        user_count_before = User.objects.count()
        out = StringIO()
        with self.assertRaises(SystemExit) as cm:
            call_command("seed_data", clear=True, stdout=out, stderr=out)
        self.assertNotEqual(cm.exception.code, 0)
        self.assertIn("not allowed outside DEBUG mode", out.getvalue())
        self.assertEqual(User.objects.count(), user_count_before)

    @override_settings(DEBUG=True)
    def test_clear_wipes_and_reseeds_when_debug_true(self):
        call_command("seed_data", stdout=StringIO())
        User.objects.all().update(elo=9999)
        call_command("seed_data", clear=True, stdout=StringIO())
        self.assertEqual(User.objects.count(), 20)
        self.assertEqual(User.objects.filter(elo=9999).count(), 0)
