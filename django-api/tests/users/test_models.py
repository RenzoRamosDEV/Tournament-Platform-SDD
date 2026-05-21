from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.users.models import User


def make_user(username="u", email=None, role="player", **kwargs):
    if email is None:
        email = f"{username}@example.com"
    return User.objects.create_user(email=email, username=username, password="x", role=role, **kwargs)


class UserFieldsTest(TestCase):
    def test_elo_defaults_to_1000(self):
        user = make_user("alice")
        self.assertEqual(user.elo, 1000)

    def test_explicit_elo_is_persisted(self):
        user = make_user("highelo", elo=1500)
        self.assertEqual(user.elo, 1500)

    def test_created_at_set_on_insert(self):
        user = make_user("alice")
        self.assertIsNotNone(user.created_at)

    def test_default_role_is_player_when_omitted(self):
        user = User.objects.create_user(email="x@x.com", username="x", password="x")
        self.assertEqual(user.role, "player")

    def test_default_elo_is_1000_when_omitted(self):
        user = User.objects.create_user(email="y@y.com", username="y", password="x")
        self.assertEqual(user.elo, 1000)

    def test_email_field_is_stored(self):
        user = make_user("alice", email="alice@example.com")
        self.assertEqual(user.email, "alice@example.com")

    def test_avatar_url_is_optional(self):
        user = make_user("noavatar")
        self.assertIsNone(user.avatar_url)

    def test_avatar_url_can_be_set(self):
        user = make_user("avatarid", avatar_url="https://example.com/avatar.png")
        self.assertEqual(user.avatar_url, "https://example.com/avatar.png")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields_contains_username(self):
        self.assertIn("username", User.REQUIRED_FIELDS)

    def test_user_is_persisted_to_database(self):
        make_user("saved")
        self.assertTrue(User.objects.filter(username="saved").exists())

    def test_password_is_hashed_not_plaintext(self):
        user = make_user("hashed")
        self.assertNotEqual(user.password, "x")
        self.assertTrue(user.check_password("x"))

    def test_password_none_does_not_verify_as_real_password(self):
        user = make_user("nullpw")
        self.assertFalse(user.check_password(None))


class UserRoleTest(TestCase):
    def test_admin_role_accepted(self):
        user = make_user("admin1", role="admin")
        self.assertEqual(user.role, "admin")

    def test_organizer_role_accepted(self):
        user = make_user("org1", role="organizer")
        self.assertEqual(user.role, "organizer")

    def test_player_role_accepted(self):
        user = make_user("player1", role="player")
        self.assertEqual(user.role, "player")

    def test_invalid_role_raises_validation_error_on_full_clean(self):
        user = User(username="bad", email="bad@example.com", role="referee", elo=1000)
        user.set_password("secret")
        with self.assertRaises(ValidationError):
            user.full_clean()


class UserUniqueConstraintsTest(TestCase):
    def test_duplicate_username_raises_integrity_error(self):
        make_user("bob")
        with self.assertRaises(IntegrityError):
            make_user("bob", email="bob2@example.com")

    def test_duplicate_email_raises_integrity_error(self):
        make_user("alice", email="alice@example.com")
        with self.assertRaises(IntegrityError):
            make_user("alice2", email="alice@example.com")


class UserManagerTest(TestCase):
    def test_create_user_sets_is_staff_false(self):
        user = make_user("u1")
        self.assertFalse(user.is_staff)

    def test_create_user_sets_is_superuser_false(self):
        user = make_user("u2")
        self.assertFalse(user.is_superuser)

    def test_create_superuser_sets_is_staff(self):
        su = User.objects.create_superuser(email="su@example.com", username="su", password="pw")
        self.assertTrue(su.is_staff)

    def test_create_superuser_sets_is_superuser(self):
        su = User.objects.create_superuser(email="su2@example.com", username="su2", password="pw")
        self.assertTrue(su.is_superuser)

    def test_create_superuser_defaults_role_to_admin(self):
        su = User.objects.create_superuser(email="su3@example.com", username="su3", password="pw")
        self.assertEqual(su.role, "admin")

    def test_create_superuser_password_is_hashed(self):
        su = User.objects.create_superuser(email="su4@example.com", username="su4", password="strongpw")
        self.assertTrue(su.check_password("strongpw"))


class UserDeletionTest(TestCase):
    def test_user_deletion_blocked_when_owns_team(self):
        from django.db.models.deletion import ProtectedError

        from apps.teams.models import Team
        owner = make_user("owner")
        Team.objects.create(name="Alpha", owner=owner)
        with self.assertRaises(ProtectedError):
            owner.delete()

    def test_user_deletion_cascades_team_memberships(self):
        from apps.teams.models import Team, TeamMember
        owner = make_user("owner2")
        member = make_user("member2")
        team = Team.objects.create(name="Beta", owner=owner)
        TeamMember.objects.create(user=member, team=team)
        member_id = member.pk
        member.delete()
        self.assertFalse(TeamMember.objects.filter(user_id=member_id).exists())
