from django.db import IntegrityError
from django.test import TestCase

from apps.teams.models import Team, TeamMember
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
