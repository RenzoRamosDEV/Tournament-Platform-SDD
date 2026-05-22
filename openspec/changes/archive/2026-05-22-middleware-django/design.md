## Context

Django's auth is currently split: `djangorestframework-simplejwt` issues tokens (via `/api/token/`) and validates them on each DRF request using `JWTAuthentication`. The Java `auth-service` now owns this responsibility. This change is purely a Django-side wiring task — no Java changes needed.

The middleware pattern is chosen over a DRF authentication class because it runs before DRF and sets `request.user` in a way that's transparent to all views and permissions, including non-DRF views.

## Goals / Non-Goals

**Goals:**
- Replace simplejwt with a thin HTTP call to the Java auth service
- Keep the change invisible to views — they still use `request.user` and DRF permissions unchanged
- Remove all simplejwt footprint from the codebase

**Non-Goals:**
- Caching validated tokens (every request calls Java — acceptable for now)
- Modifying the Java auth service
- Changing any view permission logic

## Decisions

### D1: Django middleware over DRF authentication class
**Decision**: Implement as a standard Django WSGI middleware (`__init__` / `__call__` pattern), not a DRF `BaseAuthentication` subclass.  
**Rationale**: Middleware runs before DRF and covers all requests uniformly. A DRF auth class only runs when DRF processes the view, missing non-DRF routes. Also avoids DRF's auth exception handling which returns `WWW-Authenticate` headers we don't want.  
**Trade-off**: Middleware can't use DRF's `request.auth` slot, but `request.user` is sufficient.

### D2: Real DB User lookup (not a lightweight object)
**Decision**: After Java returns `valid: true`, look up `User.objects.get(email__iexact=email)` and set that as `request.user`.  
**Rationale**: DRF permission classes (`IsAuthenticated`, custom role checks) expect a real `User` instance with `.is_authenticated = True`. A synthetic object would break all existing permission checks.  
**Trade-off**: One extra DB query per authenticated request. Acceptable — the Java call already dominates latency.

### D3: 503 for Java service failures, 401 for bad tokens
**Decision**: Connection errors, `requests.Timeout`, and HTTP 5xx → `503`. `valid: false` from Java → `401`.  
**Rationale**: Lets clients distinguish "your token is wrong" (retry with fresh login) from "the service is temporarily down" (retry the same request later). Standard REST error semantics.

### D4: No token → AnonymousUser, not 401
**Decision**: Missing `Authorization` header sets `request.user = AnonymousUser()` and passes through.  
**Rationale**: Some endpoints may be public. The view (via `IsAuthenticated`) is the right place to enforce auth requirements, not the middleware.

### D5: `AUTH_SERVICE_URL` from Django settings
**Decision**: `http://java-auth:8080` is read from `settings.AUTH_SERVICE_URL`, not hardcoded.  
**Rationale**: Different environments (local, staging, prod) use different host names. Settings is the correct Django extension point.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Java service down makes all authenticated endpoints return 503 | Acceptable — auth is a hard dependency. Document 503 in API contract. |
| 2s timeout adds latency to every authenticated request on a slow network | Acceptable for a learning project. Can be made configurable later. |
| Tests using simplejwt setup break immediately after removal | All affected tests updated in the same task group. |

## Migration Plan

1. Write and test `JwtAuthMiddleware` with the Java service stubbed (unit tests with `unittest.mock`)
2. Remove simplejwt from settings, URLs, requirements
3. Update all affected tests
4. Run full test suite — all tests must pass
