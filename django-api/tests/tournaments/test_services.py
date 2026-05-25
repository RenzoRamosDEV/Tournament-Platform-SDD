import datetime

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from apps.teams.models import Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import User


def make_user(role="player", n=None):
    import random
    uid = n or random.randint(100000, 999999)
    return User.objects.create_user(
        username=f"u{uid}",
        email=f"u{uid}@test.com",
        password="secret",
        role=role,
    )


def make_team(owner=None):
    import random
    uid = random.randint(100000, 999999)
    return Team.objects.create(name=f"Team{uid}", owner=owner or make_user())


def make_tournament(status="open"):
    admin = make_user(role="admin")
    return Tournament.objects.create(
        name="TestCup",
        format="round_robin",
        max_teams=8,
        start_date=datetime.date(2026, 6, 1),
        end_date=datetime.date(2026, 6, 30),
        status=status,
        created_by=admin,
    )


def make_match(tournament=None, team_a=None, team_b=None):
    t = tournament or make_tournament()
    ta = team_a or make_team()
    tb = team_b or make_team()
    return Match.objects.create(tournament=t, team_a=ta, team_b=tb)


# ---------------------------------------------------------------------------
# MatchService tests
# ---------------------------------------------------------------------------

class MatchServiceReportResultTest(TestCase):
    def setUp(self):
        from apps.tournaments.services import MatchService
        self.service = MatchService()
        self.ta = make_team()
        self.tb = make_team()
        self.match = make_match(team_a=self.ta, team_b=self.tb)
        self.admin = make_user(role="admin")
        self.player = make_user(role="player")

    def test_successful_report_sets_fields(self):
        from apps.tournaments.services import MatchService
        MatchService.report_result(self.match.id, self.ta.id, 3, 1, is_admin=False)
        self.match.refresh_from_db()
        self.assertEqual(self.match.winner_team_id, self.ta.id)
        self.assertEqual(self.match.score_a, 3)
        self.assertEqual(self.match.score_b, 1)
        self.assertEqual(self.match.status, "finished")
        self.assertIsNotNone(self.match.played_at)

    def test_successful_report_returns_match(self):
        from apps.tournaments.services import MatchService
        result = MatchService.report_result(self.match.id, self.ta.id, 2, 0, is_admin=False)
        self.assertEqual(result.id, self.match.id)

    def test_match_not_found_raises(self):
        from apps.tournaments.services import MatchService, MatchNotFound
        with self.assertRaises(MatchNotFound):
            MatchService.report_result(99999, self.ta.id, 1, 0, is_admin=False)

    def test_already_finished_non_admin_raises(self):
        from apps.tournaments.services import MatchService, MatchAlreadyFinished
        MatchService.report_result(self.match.id, self.ta.id, 1, 0, is_admin=False)
        with self.assertRaises(MatchAlreadyFinished):
            MatchService.report_result(self.match.id, self.ta.id, 1, 0, is_admin=False)

    def test_already_finished_admin_can_overwrite(self):
        from apps.tournaments.services import MatchService
        MatchService.report_result(self.match.id, self.ta.id, 1, 0, is_admin=False)
        result = MatchService.report_result(self.match.id, self.tb.id, 0, 2, is_admin=True)
        self.assertEqual(result.winner_team_id, self.tb.id)

    def test_elo_update_triggered_on_report(self):
        from apps.tournaments.services import MatchService
        from apps.users.models import EloHistory
        member_a = make_user()
        from apps.teams.models import TeamMember
        TeamMember.objects.create(user=member_a, team=self.ta)
        MatchService.report_result(self.match.id, self.ta.id, 2, 1, is_admin=False)
        self.assertTrue(EloHistory.objects.filter(match=self.match).exists())


# ---------------------------------------------------------------------------
# TournamentService tests
# ---------------------------------------------------------------------------

class TournamentServiceTest(TestCase):
    def setUp(self):
        from apps.tournaments.services import TournamentService
        self.service = TournamentService

    def test_start_open_tournament_transitions_to_ongoing(self):
        from apps.tournaments.services import TournamentService
        t = make_tournament(status="open")
        result = TournamentService.start(t.id)
        t.refresh_from_db()
        self.assertEqual(t.status, "ongoing")
        self.assertEqual(result.id, t.id)

    def test_start_returns_updated_tournament(self):
        from apps.tournaments.services import TournamentService
        t = make_tournament(status="open")
        result = TournamentService.start(t.id)
        self.assertEqual(result.status, "ongoing")

    def test_start_draft_tournament_raises_invalid_state(self):
        from apps.tournaments.services import TournamentService, InvalidTournamentState
        t = make_tournament(status="draft")
        with self.assertRaises(InvalidTournamentState):
            TournamentService.start(t.id)

    def test_start_finished_tournament_raises_invalid_state(self):
        from apps.tournaments.services import TournamentService, InvalidTournamentState
        t = make_tournament(status="finished")
        with self.assertRaises(InvalidTournamentState):
            TournamentService.start(t.id)

    def test_start_nonexistent_tournament_raises(self):
        from apps.tournaments.services import TournamentService, TournamentNotFound
        with self.assertRaises(TournamentNotFound):
            TournamentService.start(99999)
