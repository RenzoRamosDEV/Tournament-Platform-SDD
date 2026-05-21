import datetime

from django.test import TestCase

from core.models import Match, Team, TeamMember, Tournament, TournamentTeam, User
from core.serializers import (
    MatchReportSerializer,
    MatchSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    TournamentSerializer,
    TournamentTeamSerializer,
    UserSerializer,
)


def make_user(username="u"):
    return User.objects.create_user(
        username=username, password="secret", email=f"{username}@test.com", role="player"
    )


def make_team(name="T", owner=None):
    if owner is None:
        owner = make_user(name + "_o")
    return Team.objects.create(name=name, owner=owner)


_tourney_counter = 0


def make_tournament(name="Cup"):
    global _tourney_counter
    _tourney_counter += 1
    creator = User.objects.create_user(
        username=f"creator_{_tourney_counter}",
        password="x",
        email=f"creator{_tourney_counter}@x.com",
        role="organizer",
    )
    return Tournament.objects.create(
        name=name,
        format="single_elimination",
        max_teams=8,
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 10),
        created_by=creator,
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
            "status": "scheduled",
            "score_a": 0,
            "score_b": 0,
        })
        self.assertTrue(s.is_valid(), s.errors)


# ---------------------------------------------------------------------------
# New API serializer tests (TDD: written before implementation)
# ---------------------------------------------------------------------------

class UserSerializerApiFieldsTest(TestCase):
    """UserSerializer must expose email and avatar_url for the API."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            password="secret",
            email="api@example.com",
            role="player",
        )

    def test_email_in_output(self):
        data = UserSerializer(self.user).data
        self.assertIn("email", data)

    def test_avatar_url_in_output(self):
        data = UserSerializer(self.user).data
        self.assertIn("avatar_url", data)

    def test_all_required_api_fields_present(self):
        data = UserSerializer(self.user).data
        for field in ("id", "username", "email", "role", "elo", "avatar_url", "created_at"):
            self.assertIn(field, data, f"Missing field: {field}")

    def test_email_value_correct(self):
        data = UserSerializer(self.user).data
        self.assertEqual(data["email"], "api@example.com")


class TeamSerializerOwnerReadOnlyTest(TestCase):
    """owner field must be read-only — clients cannot set it via input data."""

    def setUp(self):
        self.owner = User.objects.create_user(username="own2", password="x", email="own2@x.com")

    def test_owner_is_read_only(self):
        s = TeamSerializer(data={"name": "Beta", "owner": self.owner.id})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn("owner", s.validated_data)

    def test_owner_present_in_serialized_output(self):
        team = Team.objects.create(name="Gamma", owner=self.owner)
        data = TeamSerializer(team).data
        self.assertIn("owner", data)
        self.assertEqual(data["owner"], self.owner.id)


class TournamentSerializerApiFieldsTest(TestCase):
    """TournamentSerializer must expose created_by and validate end_date >= start_date."""

    def setUp(self):
        self.creator = User.objects.create_user(
            username="org1", password="x", email="org1@x.com", role="organizer"
        )

    def test_created_by_in_output(self):
        t = Tournament.objects.create(
            name="Cup",
            format="round_robin",
            max_teams=8,
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
            created_by=self.creator,
        )
        data = TournamentSerializer(t).data
        self.assertIn("created_by", data)

    def test_all_required_api_fields_present(self):
        t = Tournament.objects.create(
            name="Cup2",
            format="single_elimination",
            max_teams=4,
            start_date=datetime.date(2026, 7, 1),
            end_date=datetime.date(2026, 7, 10),
            created_by=self.creator,
        )
        data = TournamentSerializer(t).data
        for field in ("id", "name", "status", "format", "max_teams", "start_date", "end_date", "created_by"):
            self.assertIn(field, data, f"Missing field: {field}")

    def test_end_date_before_start_date_invalid(self):
        s = TournamentSerializer(data={
            "name": "Bad Cup",
            "format": "round_robin",
            "max_teams": 8,
            "start_date": "2026-06-30",
            "end_date": "2026-06-01",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_end_date_equal_start_date_valid(self):
        s = TournamentSerializer(data={
            "name": "One Day Cup",
            "format": "round_robin",
            "max_teams": 4,
            "start_date": "2026-06-15",
            "end_date": "2026-06-15",
        })
        self.assertTrue(s.is_valid(), s.errors)


class MatchReportSerializerTest(TestCase):
    """MatchReportSerializer validates winner_id, score_team_a, score_team_b."""

    def setUp(self):
        owner_a = User.objects.create_user(username="oa", password="x", email="oa@x.com")
        owner_b = User.objects.create_user(username="ob", password="x", email="ob@x.com")
        self.ta = Team.objects.create(name="RA", owner=owner_a)
        self.tb = Team.objects.create(name="RB", owner=owner_b)
        creator = User.objects.create_user(username="cr", password="x", email="cr@x.com")
        self.tournament = Tournament.objects.create(
            name="RC",
            format="round_robin",
            max_teams=4,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 10),
            created_by=creator,
        )
        self.match = Match.objects.create(
            tournament=self.tournament,
            team_a=self.ta,
            team_b=self.tb,
        )

    def test_valid_winner_team_a(self):
        s = MatchReportSerializer(
            data={"winner_id": self.ta.id, "score_team_a": 3, "score_team_b": 1},
            context={"match": self.match},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_winner_team_b(self):
        s = MatchReportSerializer(
            data={"winner_id": self.tb.id, "score_team_a": 0, "score_team_b": 2},
            context={"match": self.match},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_winner_not_in_match(self):
        other_owner = User.objects.create_user(username="ox", password="x", email="ox@x.com")
        other = Team.objects.create(name="Other", owner=other_owner)
        s = MatchReportSerializer(
            data={"winner_id": other.id, "score_team_a": 1, "score_team_b": 0},
            context={"match": self.match},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("winner_id", s.errors)

    def test_missing_winner_id_invalid(self):
        s = MatchReportSerializer(
            data={"score_team_a": 1, "score_team_b": 0},
            context={"match": self.match},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("winner_id", s.errors)

    def test_negative_score_invalid(self):
        s = MatchReportSerializer(
            data={"winner_id": self.ta.id, "score_team_a": -1, "score_team_b": 0},
            context={"match": self.match},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("score_team_a", s.errors)
