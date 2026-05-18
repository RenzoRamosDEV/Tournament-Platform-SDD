import datetime

from django.test import TestCase

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User
from core.serializers import (
    MatchSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    TournamentSerializer,
    TournamentTeamSerializer,
    UserSerializer,
)


def make_user(username="u"):
    return User.objects.create_user(username=username, password="secret", role="player")


def make_team(name="T", owner=None):
    if owner is None:
        owner = make_user(name + "_o")
    return Team.objects.create(name=name, owner=owner)


def make_tournament():
    return Tournament.objects.create(
        name="Cup",
        format="single_elim",
        max_teams=8,
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 10),
    )


class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = make_user("alice")

    def test_contains_expected_fields(self):
        data = UserSerializer(self.user).data
        for field in ("id", "username", "role", "elo", "created_at"):
            self.assertIn(field, data)

    def test_password_not_in_output(self):
        data = UserSerializer(self.user).data
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_read_only_fields(self):
        s = UserSerializer(data={"username": "bob", "role": "player", "password": "x"})
        self.assertTrue(s.is_valid(), s.errors)


class TeamSerializerTest(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.team = make_team("Alpha", owner=self.owner)

    def test_contains_expected_fields(self):
        data = TeamSerializer(self.team).data
        for field in ("id", "name", "owner", "created_at"):
            self.assertIn(field, data)


class TeamMemberSerializerTest(TestCase):
    def setUp(self):
        owner = make_user("own")
        member = make_user("mem")
        team = make_team("T1", owner=owner)
        self.tm = TeamMember.objects.create(user=member, team=team)

    def test_contains_expected_fields(self):
        data = TeamMemberSerializer(self.tm).data
        for field in ("user", "team", "joined_at"):
            self.assertIn(field, data)


class TournamentSerializerTest(TestCase):
    def setUp(self):
        self.tournament = make_tournament()

    def test_contains_expected_fields(self):
        data = TournamentSerializer(self.tournament).data
        for field in ("id", "name", "status", "format", "max_teams", "start_date", "end_date"):
            self.assertIn(field, data)

    def test_status_default_in_output(self):
        data = TournamentSerializer(self.tournament).data
        self.assertEqual(data["status"], "draft")


class TournamentTeamSerializerTest(TestCase):
    def setUp(self):
        t = make_tournament()
        team = make_team()
        self.tt = TournamentTeam.objects.create(tournament=t, team=team)

    def test_contains_expected_fields(self):
        data = TournamentTeamSerializer(self.tt).data
        for field in ("tournament", "team", "registered_at"):
            self.assertIn(field, data)


class MatchSerializerUpdateTest(TestCase):
    """Tests that exercise the instance-path (PATCH/PUT) in MatchSerializer.validate."""

    def setUp(self):
        self.tournament = make_tournament()
        self.ta = make_team("UA")
        self.tb = make_team("UB")
        self.tc = make_team("UC")
        self.match = Match.objects.create(
            tournament=self.tournament, team_a=self.ta, team_b=self.tb
        )

    def test_update_winner_to_team_b_valid(self):
        s = MatchSerializer(
            self.match,
            data={"winner_team": self.tb.id, "status": "finished"},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_update_winner_to_third_team_invalid(self):
        s = MatchSerializer(
            self.match,
            data={"winner_team": self.tc.id, "status": "finished"},
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("winner_team", s.errors)

    def test_error_message_key_is_winner_team(self):
        s = MatchSerializer(data={
            "tournament": make_tournament().id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.tc.id,
            "status": "finished",
            "score_a": 0,
            "score_b": 0,
        })
        s.is_valid()
        self.assertIn("winner_team", s.errors)

    def test_update_winner_only_team_b_provided_in_data(self):
        """team_b not in partial data — must use instance.team_b path."""
        # winner_team is team_b (not in partial update data)
        s = MatchSerializer(
            self.match,
            data={"winner_team": self.tb.id, "status": "finished"},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_update_invalid_winner_with_only_winner_in_data(self):
        """Neither team_a nor team_b in partial data — invalid winner via instance path."""
        s = MatchSerializer(
            self.match,
            data={"winner_team": self.tc.id},
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("winner_team", s.errors)


class MatchSerializerTest(TestCase):
    def setUp(self):
        self.tournament = make_tournament()
        self.ta = make_team("A")
        self.tb = make_team("B")
        self.tc = make_team("C")

    def test_contains_expected_fields(self):
        m = Match.objects.create(tournament=self.tournament, team_a=self.ta, team_b=self.tb)
        data = MatchSerializer(m).data
        for field in ("id", "tournament", "team_a", "team_b", "winner_team", "score_a", "score_b", "status", "played_at"):
            self.assertIn(field, data)

    def test_invalid_winner_raises_validation_error(self):
        s = MatchSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.tc.id,
            "status": "finished",
            "score_a": 1,
            "score_b": 0,
        })
        self.assertFalse(s.is_valid())
        self.assertIn("winner_team", s.errors)

    def test_invalid_winner_error_message_text(self):
        s = MatchSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.tc.id,
            "status": "finished",
            "score_a": 0,
            "score_b": 0,
        })
        s.is_valid()
        msg = str(s.errors["winner_team"])
        self.assertIn("winner_team", msg.lower())
        self.assertIn("team_a", msg.lower())
        self.assertIn("team_b", msg.lower())
        # Exact case must be lowercase (kills message-case mutations)
        self.assertNotIn("XX", msg)
        self.assertNotEqual(msg, msg.upper())
        # Message should be readable sentence case (not all-caps)
        self.assertIn("must be", msg)

    def test_valid_winner_passes_validation(self):
        s = MatchSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.ta.id,
            "status": "finished",
            "score_a": 1,
            "score_b": 0,
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_winner_is_team_b_passes_validation(self):
        s = MatchSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "winner_team": self.tb.id,
            "status": "finished",
            "score_a": 0,
            "score_b": 1,
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_null_winner_passes_validation(self):
        s = MatchSerializer(data={
            "tournament": self.tournament.id,
            "team_a": self.ta.id,
            "team_b": self.tb.id,
            "status": "pending",
            "score_a": 0,
            "score_b": 0,
        })
        self.assertTrue(s.is_valid(), s.errors)
