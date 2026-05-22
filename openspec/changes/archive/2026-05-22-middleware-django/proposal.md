## Why

Django currently issues and validates JWTs itself via `djangorestframework-simplejwt`, duplicating auth logic that now lives in the Java `auth-service`. This change wires Django up to the Java service for all token validation, making Java the single source of truth and Django a stateless API server that never touches JWT secrets.

## What Changes

- A new `JwtAuthMiddleware` is introduced in `app/middleware/jwt_auth.py`
- On every request the middleware extracts the Bearer token, calls `POST /auth/validate` on the Java service, and sets `request.user` to the matching Django `User` (DB lookup by email) or `AnonymousUser`
- Invalid tokens → `401`; Java service down/timeout → `503`; no token → pass-through with `AnonymousUser`
- `djangorestframework-simplejwt` is removed: package, settings, URL patterns, and all imports
- `DEFAULT_AUTHENTICATION_CLASSES` is cleared; auth is now entirely in the middleware
- Existing tests are updated to stub `request.user` rather than minting simplejwt tokens

## Capabilities

### New Capabilities
- `django-jwt-middleware`: Middleware that validates bearer tokens by calling the Java auth service and injects the authenticated `User` into every request

### Modified Capabilities
- `django-project-setup`: `simplejwt` is removed from installed apps, settings, and URL patterns; `AUTH_SERVICE_URL` is added to settings; `JwtAuthMiddleware` is added to `MIDDLEWARE`

## Impact

- **New file**: `django-api/app/middleware/jwt_auth.py`
- **New file**: `django-api/tests/test_jwt_middleware.py`
- **Modified**: `django-api/app/settings.py` (or equivalent) — remove `SIMPLE_JWT`, add `AUTH_SERVICE_URL`, update `MIDDLEWARE` and `REST_FRAMEWORK`
- **Modified**: `django-api/app/urls.py` — remove simplejwt token URL patterns
- **Modified**: `django-api/requirements/` — remove `djangorestframework-simplejwt`
- **Modified**: All test files that use simplejwt for authentication setup
- **No DB migrations required**
