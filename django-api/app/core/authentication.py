from rest_framework.authentication import BaseAuthentication


class JavaJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None
