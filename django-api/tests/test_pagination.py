import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.teams.models import Team
from apps.tournaments.models import Tournament
from apps.users.models import User


def make_admin():
    return User.objects.create_user(
        username="pa_admin", email="pa_admin@test.com", password="x", role="admin"
    )


def make_team(n, owner):
    return Team.objects.create(name=f"PTeam{n}", owner=owner)


class GlobalPaginationTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.teams = [make_team(i, self.admin) for i in range(25)]
        self.client = APIClient()

    def test_default_page_size_is_20(self):
        response = self.client.get("/api/teams/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 20)

    def test_page_size_override_works(self):
        response = self.client.get("/api/teams/?page_size=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 5)

    def test_page_size_clamped_to_max_100(self):
        # ensure enough items beyond 100
        for i in range(80):
            Team.objects.get_or_create(name=f"XTeam{i}", defaults={"owner": self.admin})
        response = self.client.get("/api/teams/?page_size=200")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()["results"]), 100)

    def test_pagination_envelope_present(self):
        response = self.client.get("/api/teams/")
        self.assertEqual(response.status_code, 200)
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.json())
