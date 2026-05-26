from django.db import IntegrityError
from django.test import TestCase

import datetime

from apps.teams.models import EloHistory, Team, TeamMember
from apps.users.models import User


def make_user(username="u", role="player"):
    return User.objects.create_user(
        email=f"{username}@example.com", username=username, password="x", role=role
    )


class TeamCreationTest(TestCase):
    def test_team_created_with_owner(self):
        owner = make_user("owner")
        team = Team.objects.create(name="Alpha", owner=owner)
        self.assertEqual(team.owner, owner)
        self.assertIsNotNone(team.created_at)

    def test_duplicate_team_name_rejected(self):
        owner = make_user("owner")
        Team.objects.create(name="Alpha", owner=owner)
        with self.assertRaises(IntegrityError):
            Team.objects.create(name="Alpha", owner=owner)

    def test_owner_not_auto_added_as_member(self):
        owner = make_user("owner")
        Team.objects.create(name="Alpha", owner=owner)
        self.assertEqual(TeamMember.objects.count(), 0)


class TeamEloFieldTest(TestCase):
    def test_new_team_has_default_elo_1000(self):
        owner = make_user("elo_owner")
        team = Team.objects.create(name="EloTeam", owner=owner)
        self.assertEqual(team.elo, 1000)

    def test_elo_field_can_be_updated(self):
        owner = make_user("elo_owner2")
        team = Team.objects.create(name="EloTeam2", owner=owner)
        team.elo = 1200
        team.save(update_fields=["elo"])
        team.refresh_from_db()
        self.assertEqual(team.elo, 1200)


class TeamMemberTest(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.member = make_user("member")
        self.team = Team.objects.create(name="Alpha", owner=self.owner)

    def test_member_added_with_joined_at(self):
        tm = TeamMember.objects.create(user=self.member, team=self.team)
        self.assertIsNotNone(tm.joined_at)

    def test_duplicate_membership_rejected(self):
        TeamMember.objects.create(user=self.member, team=self.team)
        with self.assertRaises(IntegrityError):
            TeamMember.objects.create(user=self.member, team=self.team)

    def test_delete_team_cascades_members(self):
        TeamMember.objects.create(user=self.member, team=self.team)
        team_id = self.team.pk
        self.team.delete()
        self.assertFalse(TeamMember.objects.filter(team_id=team_id).exists())


def make_match(team_a, team_b):
    from apps.tournaments.models import Match, Tournament
    admin = make_user("t_admin")
    t = Tournament.objects.create(
        name="Cup",
        format="round_robin",
        max_teams=4,
        start_date=datetime.date(2026, 6, 1),
        end_date=datetime.date(2026, 6, 30),
        status="open",
        created_by=admin,
    )
    return Match.objects.create(tournament=t, team_a=team_a, team_b=team_b)


class EloHistoryModelTest(TestCase):
    def setUp(self):
        owner_a = make_user("ha")
        owner_b = make_user("hb")
        self.team_a = Team.objects.create(name="HistA", owner=owner_a)
        self.team_b = Team.objects.create(name="HistB", owner=owner_b)
        self.match = make_match(self.team_a, self.team_b)

    def test_elohistory_created_with_required_fields(self):
        h = EloHistory.objects.create(
            team=self.team_a,
            match=self.match,
            elo_before=1000,
            elo_after=1016,
        )
        self.assertEqual(h.elo_before, 1000)
        self.assertEqual(h.elo_after, 1016)
        self.assertIsNotNone(h.created_at)

    def test_duplicate_team_match_rejected(self):
        EloHistory.objects.create(
            team=self.team_a, match=self.match, elo_before=1000, elo_after=1016
        )
        with self.assertRaises(IntegrityError):
            EloHistory.objects.create(
                team=self.team_a, match=self.match, elo_before=1000, elo_after=1016
            )

    def test_cascades_on_match_delete(self):
        EloHistory.objects.create(
            team=self.team_a, match=self.match, elo_before=1000, elo_after=1016
        )
        match_id = self.match.pk
        self.match.delete()
        self.assertFalse(EloHistory.objects.filter(match_id=match_id).exists())
