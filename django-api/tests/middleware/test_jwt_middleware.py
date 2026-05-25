import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.users.models import User
from app.middleware.jwt_auth import JwtAuthMiddleware

AUTH_URL = "http://test-java:8080"


def _get_response(request):
    return HttpResponse("ok", status=200)


def make_middleware():
    return JwtAuthMiddleware(_get_response)


@override_settings(AUTH_SERVICE_URL=AUTH_URL)
class JwtAuthMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="mwuser", email="mw@example.com", password="pass"
        )

    # --- No Authorization header ---

    def test_no_auth_header_sets_anonymous_user(self):
        request = self.factory.get("/api/users/")
        response = make_middleware()(request)
        self.assertIsInstance(request.user, AnonymousUser)
        self.assertEqual(response.status_code, 200)

    # --- Valid token → user found ---

    @patch("app.middleware.jwt_auth.requests.post")
    def test_valid_token_sets_db_user(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"valid": True, "email": "mw@example.com", "role": "player"},
        )
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        make_middleware()(request)
        self.assertEqual(request.user.email, "mw@example.com")

    # --- Valid token → user NOT in DB ---

    @patch("app.middleware.jwt_auth.requests.post")
    def test_valid_token_user_not_in_db_returns_401(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"valid": True, "email": "ghost@example.com", "role": "player"},
        )
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "USER_NOT_FOUND")

    # --- Invalid token ---

    @patch("app.middleware.jwt_auth.requests.post")
    def test_invalid_token_returns_401(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"valid": False},
        )
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer badtoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "INVALID_TOKEN")

    # --- Java service timeout ---

    @patch("app.middleware.jwt_auth.requests.post", side_effect=requests.exceptions.Timeout)
    def test_java_timeout_returns_503(self, _):
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "AUTH_SERVICE_UNAVAILABLE")

    # --- Java service connection error ---

    @patch("app.middleware.jwt_auth.requests.post", side_effect=requests.exceptions.ConnectionError)
    def test_java_connection_error_returns_503(self, _):
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "AUTH_SERVICE_UNAVAILABLE")

    # --- Java returns 5xx ---

    @patch("app.middleware.jwt_auth.requests.post")
    def test_java_5xx_returns_503(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500)
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "AUTH_SERVICE_UNAVAILABLE")

    # --- Unexpected exceptions (OSError, etc.) ---

    @patch("app.middleware.jwt_auth.requests.post", side_effect=OSError("network down"))
    def test_unexpected_exception_returns_503(self, _):
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "AUTH_SERVICE_UNAVAILABLE")

    @patch("app.middleware.jwt_auth.requests.post", side_effect=RuntimeError("unexpected"))
    def test_runtime_error_never_reaches_500(self, _):
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="Bearer sometoken")
        response = make_middleware()(request)
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, 503)

    # --- Bearer scheme case-insensitive ---

    @patch("app.middleware.jwt_auth.requests.post")
    def test_bearer_scheme_case_insensitive(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"valid": True, "email": "mw@example.com", "role": "player"},
        )
        request = self.factory.get("/api/users/", HTTP_AUTHORIZATION="bearer sometoken")
        make_middleware()(request)
        self.assertEqual(request.user.email, "mw@example.com")
