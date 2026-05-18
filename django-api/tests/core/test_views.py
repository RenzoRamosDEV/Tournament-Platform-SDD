from django.test import TestCase
from django.urls import reverse


class RouterRegistrationTest(TestCase):
    """Verify all six resource endpoints are reachable (list = 200, detail requires id)."""

    LIST_URLS = [
        "user-list",
        "team-list",
        "teammember-list",
        "tournament-list",
        "tournamentteam-list",
        "match-list",
    ]

    def test_list_endpoints_return_200(self):
        for name in self.LIST_URLS:
            with self.subTest(url_name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"{name} returned {response.status_code}")

    def test_post_to_list_returns_400_or_201_not_404(self):
        for name in self.LIST_URLS:
            with self.subTest(url_name=name):
                url = reverse(name)
                response = self.client.post(url, data={}, content_type="application/json")
                self.assertNotEqual(response.status_code, 404, f"{name} POST gave 404")
