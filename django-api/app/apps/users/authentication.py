from rest_framework.authentication import BaseAuthentication


class BearerHeaderAuthentication(BaseAuthentication):
    """Provides a WWW-Authenticate: Bearer header so DRF returns 401 (not 403)
    for unauthenticated requests. Actual authentication is done by JwtAuthMiddleware."""

    def authenticate(self, request):
        return None

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
