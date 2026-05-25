from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import User


_FIVE_PER_MIN = {"anon": "5/min", "user": "60/min"}

_THROTTLE_REST = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": _FIVE_PER_MIN,
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.BearerHeaderAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}


class AnonymousThrottleTest(TestCase):
    def _make_client(self):
        from django.core.cache import cache
        cache.clear()
        c = APIClient()
        c.defaults["REMOTE_ADDR"] = "10.99.0.1"
        return c

    @override_settings(REST_FRAMEWORK=_THROTTLE_REST)
    def test_sixth_anonymous_request_returns_429(self):
        from rest_framework.throttling import SimpleRateThrottle
        with patch.object(SimpleRateThrottle, "THROTTLE_RATES", _FIVE_PER_MIN):
            client = self._make_client()
            for _ in range(5):
                response = client.get("/api/teams/")
                self.assertNotEqual(response.status_code, 429)
            response = client.get("/api/teams/")
            self.assertEqual(response.status_code, 429)

    @override_settings(REST_FRAMEWORK=_THROTTLE_REST)
    def test_429_response_includes_retry_after(self):
        from rest_framework.throttling import SimpleRateThrottle
        with patch.object(SimpleRateThrottle, "THROTTLE_RATES", _FIVE_PER_MIN):
            client = self._make_client()
            for _ in range(6):
                response = client.get("/api/teams/")
            self.assertEqual(response.status_code, 429)
            self.assertIn("Retry-After", response.headers)
