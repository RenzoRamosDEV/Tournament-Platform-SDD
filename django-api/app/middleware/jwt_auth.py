import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

from apps.users.models import User

_AUTH_TIMEOUT = 2


class JwtAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            request.user = AnonymousUser()
            return self.get_response(request)

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            request.user = AnonymousUser()
            return self.get_response(request)

        token = parts[1]
        validate_url = f"{settings.AUTH_SERVICE_URL}/auth/validate"

        try:
            resp = requests.post(validate_url, json={"token": token}, timeout=_AUTH_TIMEOUT)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return JsonResponse(
                {"error": "AUTH_SERVICE_UNAVAILABLE",
                 "message": "Authentication service is currently unavailable."},
                status=503,
            )
        except Exception:
            return JsonResponse(
                {"error": "AUTH_SERVICE_UNAVAILABLE",
                 "message": "Authentication service is currently unavailable."},
                status=503,
            )

        if resp.status_code >= 500:
            return JsonResponse(
                {"error": "AUTH_SERVICE_UNAVAILABLE",
                 "message": "Authentication service is currently unavailable."},
                status=503,
            )

        data = resp.json()

        if not data.get("valid"):
            return JsonResponse(
                {"error": "INVALID_TOKEN", "message": "Token is invalid or expired."},
                status=401,
            )

        try:
            request.user = User.objects.get(email__iexact=data["email"])
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "USER_NOT_FOUND",
                 "message": "Authenticated user does not exist in this system."},
                status=401,
            )

        return self.get_response(request)
