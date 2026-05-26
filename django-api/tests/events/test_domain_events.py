from unittest.mock import patch

import pytest
from django.test import TestCase
from rest_framework.test import force_authenticate


class MatchFinishedEventTest(TestCase):
    @patch("events.producer.publish_event")
    def test_match_finished_event_published_after_commit(self, mock_publish):
        from apps.tournaments.models import Match, Tournament
        from apps.teams.models import Team, TeamMember
        from apps.users.models import User
        from apps.tournaments.services import MatchService

        user = User.objects.create_user(email="a@a.com", username="player_a", password="x")
        team_a = Team.objects.create(name="TeamA", owner=user)
        team_b = Team.objects.create(name="TeamB", owner=user)
        TeamMember.objects.create(user=user, team=team_a)
        tournament = Tournament.objects.create(
            name="T1", format="single_elimination", max_teams=4,
            start_date="2026-01-01", end_date="2026-01-02", created_by=user,
        )
        match = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b
        )

        with self.captureOnCommitCallbacks(execute=True):
            MatchService.report_result(match.id, team_a.id, 2, 1, is_admin=False)

        assert mock_publish.called
        args = mock_publish.call_args[0]
        assert args[0] == "match.finished"
        payload = args[1]
        assert payload["match_id"] == match.id
        assert payload["team_a_id"] == team_a.id
        assert payload["team_b_id"] == team_b.id
        assert payload["winner_id"] == team_a.id

    @patch("events.producer.publish_event")
    def test_match_finished_not_published_on_service_error(self, mock_publish):
        from apps.tournaments.services import MatchService, MatchNotFound

        with pytest.raises(MatchNotFound):
            MatchService.report_result(99999, 1, 0, 0, is_admin=False)

        mock_publish.assert_not_called()


class TournamentCreatedEventTest(TestCase):
    @patch("events.producer.publish_event")
    def test_tournament_created_event_published_after_commit(self, mock_publish):
        from apps.users.models import User
        from apps.tournaments.views import TournamentViewSet
        from rest_framework.test import APIRequestFactory

        user = User.objects.create_user(email="org@a.com", username="organizer1", password="x", role="admin")
        factory = APIRequestFactory()
        request = factory.post("/", {
            "name": "Open Cup", "format": "single_elimination", "max_teams": 8,
            "start_date": "2026-06-01", "end_date": "2026-06-10",
        }, format="json")
        force_authenticate(request, user=user)

        view = TournamentViewSet.as_view({"post": "create"})
        with self.captureOnCommitCallbacks(execute=True):
            view(request)

        assert mock_publish.called
        args = mock_publish.call_args[0]
        assert args[0] == "tournament.created"
        assert "tournament_id" in args[1]
        assert args[1]["name"] == "Open Cup"


class TeamCreatedEventTest(TestCase):
    @patch("events.producer.publish_event")
    def test_team_created_event_published_after_commit(self, mock_publish):
        from apps.users.models import User
        from apps.teams.views import TeamViewSet
        from rest_framework.test import APIRequestFactory

        user = User.objects.create_user(email="owner@a.com", username="owner1", password="x")
        factory = APIRequestFactory()
        request = factory.post("/", {"name": "NewTeam"}, format="json")
        force_authenticate(request, user=user)

        view = TeamViewSet.as_view({"post": "create"})
        with self.captureOnCommitCallbacks(execute=True):
            view(request)

        assert mock_publish.called
        args = mock_publish.call_args[0]
        assert args[0] == "team.created"
        assert "team_id" in args[1]
        assert args[1]["name"] == "NewTeam"


class UserRegisteredEventTest(TestCase):
    @patch("events.producer.publish_event")
    def test_user_registered_event_published_after_commit(self, mock_publish):
        from apps.users.models import User

        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_user(email="new@a.com", username="newuser", password="pass123")

        assert mock_publish.called
        args = mock_publish.call_args[0]
        assert args[0] == "user.registered"
        assert "user_id" in args[1]
        assert args[1]["email"] == "new@a.com"
