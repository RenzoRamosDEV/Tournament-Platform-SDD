from django.db import IntegrityError
from django.test import TestCase

from core.models import User


class UserDefaultsTest(TestCase):
    def test_elo_defaults_to_1000(self):
        user = User.objects.create_user(username="alice", password="secret", role="player")
        self.assertEqual(user.elo, 1000)

    def test_created_at_set_on_insert(self):
        user = User.objects.create_user(username="alice", password="secret", role="player")
        self.assertIsNotNone(user.created_at)

    def test_admin_role_accepted(self):
        user = User.objects.create_user(username="admin1", password="secret", role="admin")
        self.assertEqual(user.role, "admin")

    def test_password_is_hashed_not_plaintext(self):
        user = User.objects.create_user(username="hashed", password="mypassword", role="player")
        self.assertNotEqual(user.password, "mypassword")
        self.assertTrue(user.check_password("mypassword"))

    def test_password_none_does_not_verify_as_real_password(self):
        user = User.objects.create_user(username="nullpw", password="realpass", role="player")
        self.assertFalse(user.check_password(None))

    def test_default_role_is_player_when_omitted(self):
        user = User.objects.create_user(username="defaultrole", password="x")
        self.assertEqual(user.role, "player")

    def test_default_elo_is_1000_when_omitted(self):
        user = User.objects.create_user(username="defaultelo", password="x")
        self.assertEqual(user.elo, 1000)

    def test_explicit_elo_is_persisted(self):
        user = User.objects.create_user(username="highelo", password="x", elo=1500)
        self.assertEqual(user.elo, 1500)

    def test_user_is_persisted_to_database(self):
        User.objects.create_user(username="saved", password="x")
        self.assertTrue(User.objects.filter(username="saved").exists())


class UserManagerSuperuserTest(TestCase):
    def test_create_superuser_sets_is_staff(self):
        su = User.objects.create_superuser(username="admin_su", password="pw")
        self.assertTrue(su.is_staff)

    def test_create_superuser_sets_is_superuser(self):
        su = User.objects.create_superuser(username="admin_su2", password="pw")
        self.assertTrue(su.is_superuser)

    def test_create_superuser_defaults_role_to_admin(self):
        su = User.objects.create_superuser(username="admin_su3", password="pw")
        self.assertEqual(su.role, "admin")

    def test_create_superuser_password_is_hashed(self):
        su = User.objects.create_superuser(username="admin_su4", password="strongpw")
        self.assertTrue(su.check_password("strongpw"))

    def test_create_superuser_custom_role_accepted(self):
        su = User.objects.create_superuser(username="admin_su5", password="pw", role="player")
        self.assertEqual(su.role, "player")


class UserUniqueUsernameTest(TestCase):
    def test_duplicate_username_raises_integrity_error(self):
        User.objects.create_user(username="bob", password="secret", role="player")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username="bob", password="other", role="player")


class UserRoleConstraintTest(TestCase):
    def test_invalid_role_raises_integrity_error(self):
        user = User(username="bad", role="superuser", elo=1000)
        user.set_password("secret")
        with self.assertRaises(Exception):
            user.save()
            # Force DB-level constraint (some backends defer)
            from django.db import connection
            connection.check_constraints()


class UserDeletionGuardTest(TestCase):
    def test_user_deletion_blocked_when_owns_team(self):
        from core.models import Team
        owner = User.objects.create_user(username="owner", password="x", role="player")
        Team.objects.create(name="Alpha", owner=owner)
        with self.assertRaises(IntegrityError):
            owner.delete()

    def test_user_deletion_blocked_when_is_member(self):
        from core.models import Team, TeamMember
        owner = User.objects.create_user(username="owner2", password="x", role="player")
        member = User.objects.create_user(username="member2", password="x", role="player")
        team = Team.objects.create(name="Beta", owner=owner)
        TeamMember.objects.create(user=member, team=team)
        with self.assertRaises(IntegrityError):
            member.delete()
