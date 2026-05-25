## Why

Both the Django+DRF tournament backend and the Spring Boot auth service were built incrementally and carry structural debt: business logic mixed into views, unguarded N+1 queries, fragile auth middleware with no fault tolerance, and insufficient test isolation. This refactor is needed now to establish a production-ready standard before feature work continues.

## What Changes

- **Django**: Extract all business logic (match result reporting, ELO calculation, tournament state transitions) into a dedicated service layer, completely decoupled from views and serializers.
- **Django**: Eliminate N+1 queries on all list endpoints using `select_related` / `prefetch_related`; query count MUST be O(1) with respect to result set size.
- **Django**: Harden JWT auth middleware with a 2-second hard timeout, structured JSON error bodies for 503/401, and zero unhandled exceptions.
- **Django**: Enforce global pagination (default 20, max 100) on all list endpoints with `page_size` override support.
- **Django**: Add rate limiting — 5 req/min unauthenticated, 60 req/min authenticated per IP — on login proxy, refresh proxy, and match result submission; respond HTTP 429 with `Retry-After`.
- **Django**: Add query filtering on tournaments, matches, and users by `status`, `date_range`, and `owner/creator id`.
- **Spring Boot**: Enforce strict three-layer architecture (Controller → Service → Repository); no business logic in Controllers or Repositories.
- **Spring Boot**: Configure Spring Security filter chain with public routes (`/auth/login`, `/auth/register`, `/auth/refresh`) and authenticated-only `/auth/validate`; return structured JSON for 401/403.
- **Spring Boot**: Implement full refresh token lifecycle — issuance on login, atomic rotation on refresh, token-family revocation on reuse, revocation on logout, rejection of expired tokens.
- **Spring Boot**: Add `@RestControllerAdvice` global exception handler producing `{ "error", "message", "timestamp" }` for all exception types.
- **Testing**: Django unit tests must mock the auth HTTP client; Spring Boot unit tests must mock repositories. Both services must reach ≥ 90% line coverage and ≥ 95% mutation score.

## Capabilities

### New Capabilities

- `django-service-layer`: Dedicated service layer for all Django business logic (match results, ELO, tournament state transitions), fully decoupled from views.
- `django-n-plus-one-guard`: O(1)-query enforcement on all list endpoints via `select_related`/`prefetch_related`, validated by query-count assertions in tests.
- `django-rate-limiting`: Per-IP rate limiting (5/min unauth, 60/min auth) on critical endpoints with HTTP 429 + `Retry-After` header.
- `spring-layered-architecture`: Strict Controller/Service/Repository separation with no business logic leaking into controllers or repositories.
- `spring-security-filter-chain`: Configured Spring Security filter chain with public/protected route split and structured JSON 401/403 responses.
- `refresh-token-lifecycle`: Full refresh token database lifecycle — issuance, atomic rotation, reuse detection with family revocation, logout revocation, expiry rejection.
- `spring-global-exception-handler`: `@RestControllerAdvice` producing uniform `{ error, message, timestamp }` JSON for all exception types.
- `mutation-testing-baseline`: Mutation score ≥ 95% for both services with surviving-mutant justification in `mutation-notes.md`.

### Modified Capabilities

- `django-jwt-middleware`: Hardening requirements added — 2-second timeout, structured 503/401 JSON error bodies, zero unhandled exceptions propagated.
- `drf-pagination`: Requirement formalized — default page size 20, max 100, `page_size` query param override required on all list endpoints.
- `drf-filtering`: Requirement extended — filtering by `status`, `date_range`, and `owner/creator id` required on tournaments, matches, and users.
- `refresh-token-revocation`: Extended to cover full token family revocation on reuse detection (previously only basic revocation).

## Impact

- **Django views**: All business logic must move out; views become thin HTTP delegators.
- **Django ORM queries**: All list querysets on `Tournament`, `Match`, `Team`, `User` relations need `select_related`/`prefetch_related` added.
- **Django middleware**: `JWTAuthMiddleware` (or equivalent) hardened with timeout, error handling, and structured responses.
- **Spring Boot controllers**: Business logic stripped; must delegate entirely to services.
- **Spring Boot security config**: `SecurityFilterChain` bean added/replaced.
- **Spring Boot entities**: `RefreshToken` entity and repository added for token lifecycle persistence.
- **Spring Boot exception handling**: New `@RestControllerAdvice` class added.
- **Test suites (both)**: Coverage and mutation score targets enforced; mock/fake strategies locked in.
