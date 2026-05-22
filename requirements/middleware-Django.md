# Requirements: Django JWT Middleware — Java Auth Integration

## Purpose
Django currently validates JWTs itself via `djangorestframework-simplejwt`. This change replaces that with a custom middleware that delegates all token verification to the Java `auth-service`. Django becomes a pure API server with no knowledge of JWT secrets or signing logic — the Java service is the single source of truth for authentication. This also removes the `djangorestframework-simplejwt` dependency entirely.

## Scope
- **In scope:**
  - A new Django middleware class (`JwtAuthMiddleware`) that intercepts every request
  - Extraction of the Bearer token from the `Authorization` header
  - An internal HTTP `POST` call to `http://java-auth:8080/auth/validate` with a 2-second timeout
  - Setting `request.user` to the matching Django `User` model instance (looked up by email from the token claims) when the token is valid
  - Setting `request.user` to `AnonymousUser` when no `Authorization` header is present
  - Returning `401 Unauthorized` when the token is present but invalid or expired
  - Returning `503 Service Unavailable` when the Java auth service is unreachable or returns a 5xx
  - Removing `djangorestframework-simplejwt` from `requirements.txt` and all Django settings/URLs
  - Wiring `JwtAuthMiddleware` into `MIDDLEWARE` in Django settings

- **Out of scope:**
  - Issuing or refreshing tokens (Java service owns this)
  - Caching or locally re-validating JWT signatures in Django
  - Role-based access control within the middleware (views remain responsible for permission checks)
  - Changes to the Java `auth-service`
  - Rate limiting or brute-force protection on the middleware level

## Requirements

1. The middleware MUST be implemented as a Django middleware class named `JwtAuthMiddleware` in `app/middleware/jwt_auth.py`.

2. For every incoming request, the middleware MUST check for an `Authorization` header with the format `Bearer <token>`. Header matching MUST be case-insensitive on the scheme name (`bearer`, `Bearer`, `BEARER` are all valid).

3. If the `Authorization` header is absent, the middleware MUST set `request.user = AnonymousUser()` and call `get_response(request)` without blocking the request.

4. If the `Authorization` header is present, the middleware MUST send a `POST` request to `http://java-auth:8080/auth/validate` with body `{ "token": "<extracted_token>" }` and a connection+read timeout of exactly 2 seconds.

5. The Java auth service URL MUST be read from the `AUTH_SERVICE_URL` Django setting (e.g. `http://java-auth:8080`), not hardcoded in the middleware. The default value in settings is `http://java-auth:8080`.

6. If the Java service responds with `{ "valid": true, "email": "...", "role": "..." }`, the middleware MUST look up the Django `User` by `email` (exact match, case-insensitive). If the user exists, `request.user` MUST be set to that `User` instance. If no matching user exists in the Django DB, the middleware MUST return `401 Unauthorized` with body `{ "error": "USER_NOT_FOUND", "message": "Authenticated user does not exist in this system." }`.

7. If the Java service responds with `{ "valid": false }`, the middleware MUST return `401 Unauthorized` with body `{ "error": "INVALID_TOKEN", "message": "Token is invalid or expired." }`.

8. If the Java service call raises a connection error, timeout (`requests.exceptions.Timeout`), or returns an HTTP 5xx status, the middleware MUST return `503 Service Unavailable` with body `{ "error": "AUTH_SERVICE_UNAVAILABLE", "message": "Authentication service is currently unavailable." }`.

9. The middleware MUST use the `requests` library for the HTTP call to the Java service. The `requests` library MUST already be present in the project dependencies (it is).

10. After removing `djangorestframework-simplejwt`: all `simplejwt` imports, URL patterns (`/api/token/`, `/api/token/refresh/`), and settings entries (`SIMPLE_JWT`, `rest_framework.authentication.JWTAuthentication`) MUST be deleted from the codebase.

11. The `DEFAULT_AUTHENTICATION_CLASSES` in `REST_FRAMEWORK` settings MUST be cleared or removed (authentication is now handled by the middleware, not DRF authentication classes).

12. All existing tests that mock or use `simplejwt` token generation for authentication MUST be updated to use a fake/stub `request.user` or a test helper that bypasses the middleware.

## Scenarios

### Valid Token — User Found
- GIVEN a request with `Authorization: Bearer <valid_jwt>`
- WHEN the Java service returns `{ "valid": true, "email": "player@example.com", "role": "player" }`
- THEN `request.user` is set to the Django `User` instance with that email and the request proceeds normally

### Valid Token — User Not in Django DB
- GIVEN a request with a valid JWT whose email does not match any row in the Django `users` table
- WHEN the Java service returns `{ "valid": true, "email": "ghost@example.com", "role": "player" }`
- THEN the middleware returns `401 Unauthorized` with `{ "error": "USER_NOT_FOUND" }`

### Invalid or Expired Token
- GIVEN a request with `Authorization: Bearer <expired_or_tampered_jwt>`
- WHEN the Java service returns `{ "valid": false }`
- THEN the middleware returns `401 Unauthorized` with `{ "error": "INVALID_TOKEN", "message": "Token is invalid or expired." }`

### No Authorization Header
- GIVEN a request with no `Authorization` header
- WHEN the middleware processes the request
- THEN `request.user` is set to `AnonymousUser()` and the request is passed to the next handler unchanged

### Java Service Timeout
- GIVEN the Java auth service does not respond within 2 seconds
- WHEN the middleware's HTTP call raises `requests.exceptions.Timeout`
- THEN the middleware returns `503 Service Unavailable` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`

### Java Service Returns 5xx
- GIVEN the Java auth service responds with HTTP 500
- WHEN the middleware receives that response
- THEN the middleware returns `503 Service Unavailable` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`

### Bearer Scheme Case-Insensitive
- GIVEN a request with `Authorization: bearer <valid_jwt>` (lowercase)
- WHEN the middleware processes the header
- THEN the token is extracted correctly and validated as normal

### simplejwt Removed
- GIVEN the middleware is wired into `MIDDLEWARE`
- WHEN the Django app starts
- THEN no `simplejwt` import, URL pattern, or setting entry exists anywhere in the codebase

## Open Questions

- **Email case sensitivity in DB lookup:** Django's `User` model uses `iexact` for email lookups in `AbstractBaseUser`. Confirm the `users` table has a `UNIQUE` constraint that is case-insensitive, or clarify if exact-match is acceptable. (Current Django model uses `unique=True` on `EmailField` which is case-insensitive in most DB collations.)
