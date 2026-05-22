## 1. Middleware — Failing Tests First

- [x] 1.1 Create `django-api/app/middleware/__init__.py` (empty) and `django-api/tests/middleware/__init__.py`
- [x] 1.2 Write failing test: no `Authorization` header → `request.user` is `AnonymousUser` and request passes through
- [x] 1.3 Write failing test: valid token → Java returns `{ "valid": true, ... }` → `request.user` is the matching Django `User` instance
- [x] 1.4 Write failing test: valid token → Java returns `{ "valid": true, ... }` but email not in DB → `401` with `USER_NOT_FOUND`
- [x] 1.5 Write failing test: invalid token → Java returns `{ "valid": false }` → `401` with `INVALID_TOKEN`
- [x] 1.6 Write failing test: Java call raises `requests.exceptions.Timeout` → `503` with `AUTH_SERVICE_UNAVAILABLE`
- [x] 1.7 Write failing test: Java call raises `requests.exceptions.ConnectionError` → `503` with `AUTH_SERVICE_UNAVAILABLE`
- [x] 1.8 Write failing test: Java returns HTTP 500 → `503` with `AUTH_SERVICE_UNAVAILABLE`
- [x] 1.9 Write failing test: `Authorization: bearer <token>` (lowercase) → token extracted and validated normally

## 2. Middleware — Implementation

- [x] 2.1 Implement `JwtAuthMiddleware` in `django-api/app/middleware/jwt_auth.py`:
  - Extract Bearer token from `Authorization` header (case-insensitive scheme)
  - If no header: set `request.user = AnonymousUser()`, call `get_response`
  - POST to `{settings.AUTH_SERVICE_URL}/auth/validate` with `{"token": token}` and `timeout=2`
  - On `valid: true`: look up `User.objects.get(email__iexact=email)` and set `request.user`
  - On `valid: true` + no DB user: return `JsonResponse({"error": "USER_NOT_FOUND", ...}, status=401)`
  - On `valid: false`: return `JsonResponse({"error": "INVALID_TOKEN", ...}, status=401)`
  - On `Timeout`, `ConnectionError`, or 5xx: return `JsonResponse({"error": "AUTH_SERVICE_UNAVAILABLE", ...}, status=503)`

## 3. Settings and Wiring

- [x] 3.1 Add `AUTH_SERVICE_URL = config("AUTH_SERVICE_URL", default="http://java-auth:8080")` to `django-api/app/config/settings/base.py`
- [x] 3.2 Add `"app.middleware.jwt_auth.JwtAuthMiddleware"` to `MIDDLEWARE` in `base.py`, immediately after `CorsMiddleware`
- [x] 3.3 Clear `DEFAULT_AUTHENTICATION_CLASSES` in `REST_FRAMEWORK` to `[]` (the stub `JavaJWTAuthentication` class can be deleted)
- [x] 3.4 Delete `django-api/app/apps/users/authentication.py` (the stub `JavaJWTAuthentication` is replaced by the middleware)

## 4. Final Verification

- [x] 4.1 Run `pytest django-api/tests/middleware/` and confirm all middleware tests pass
- [x] 4.2 Run the full Django test suite (`pytest django-api/`) and confirm no regressions
