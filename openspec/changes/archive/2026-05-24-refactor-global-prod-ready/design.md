## Context

The tournament platform consists of two services: a Django+DRF backend and a Spring Boot auth service. Both were developed iteratively, accumulating structural debt. The Django backend has views that contain business logic, list endpoints with N+1 query patterns, a JWT middleware that lacks timeout and error handling, and missing pagination/filtering/rate-limiting. The Spring Boot service lacks strict layering, has no refresh token persistence, no token family revocation, and no global exception handler. Test coverage and mutation scores are below production standards.

This design covers both services simultaneously since the refactor is structural and must be coherent across the codebase.

## Goals / Non-Goals

**Goals:**
- Establish a clear service layer in Django, removing all business logic from views and serializers.
- Eliminate N+1 ORM queries with `select_related`/`prefetch_related` and guard them via test-time query count assertions.
- Harden the Django JWT middleware with timeout, structured error responses, and zero unhandled exceptions.
- Enforce global pagination and per-IP rate limiting across all relevant Django endpoints.
- Add query filtering (status, date_range, owner/creator id) to list endpoints.
- Enforce three-layer architecture in Spring Boot (Controller/Service/Repository).
- Implement a fully persisted refresh token lifecycle with atomic rotation and token family revocation.
- Add a `@RestControllerAdvice` global exception handler with uniform JSON error structure.
- Bring both services to ≥ 90% line coverage and ≥ 95% mutation score.

**Non-Goals:**
- New business features (tournament types, ELO formula changes).
- Database schema changes beyond adding the `refresh_tokens` table.
- Frontend/client changes.
- Infrastructure, CI/CD, or deployment configuration.
- Third-party auth providers (OAuth2, SSO).

## Decisions

### D1: Django Service Layer — Module vs. Package
**Decision:** Use a `services.py` module per Django app initially; promote to a `services/` package only if a single module exceeds ~300 lines.

**Rationale:** Apps like `matches`, `tournaments`, and `users` each have bounded logic. A flat `services.py` per app keeps the structure discoverable without premature abstraction. If logic grows, the package promotion is a mechanical rename with no API change.

**Alternative considered:** A top-level `services/` package. Rejected because it blurs app ownership and makes import paths less obvious.

---

### D2: N+1 Guard — QuerySet annotation vs. select/prefetch
**Decision:** Use `select_related` for FK traversals and `prefetch_related` for M2M/reverse FK. Do NOT use `annotate` as a substitute for prefetch unless aggregation is the goal.

**Rationale:** `select_related` generates a JOIN and is appropriate for single-valued relations. `prefetch_related` uses separate queries but batches them into O(1) queries regardless of result count. `annotate` is appropriate for computed fields, not for eager-loading related objects.

**Guard mechanism:** Django's `django.test.utils.CaptureQueriesContext` (or `assertNumQueries`) in integration tests ensures query count does not regress.

---

### D3: JWT Middleware Hardening — requests timeout + structured responses
**Decision:** Use `requests.get(..., timeout=2)` with explicit `try/except` covering `requests.Timeout`, `requests.ConnectionError`, and catch-all `Exception`. Return `JsonResponse` with the specified error bodies; never re-raise.

**Rationale:** A 2-second timeout is specified in requirements. Using `requests` (already a dependency) keeps consistency. Catching `Exception` as a last resort ensures the middleware never propagates to Django's 500 handler.

**Alternative considered:** `httpx` with async support. Rejected because the middleware is synchronous and introducing `httpx` adds a dependency without benefit here.

---

### D4: Rate Limiting — django-ratelimit vs. DRF throttling
**Decision:** Use DRF's built-in throttling (`AnonRateThrottle`, `UserRateThrottle`) configured globally in `DEFAULT_THROTTLE_CLASSES` and `DEFAULT_THROTTLE_RATES`, with per-view overrides for critical endpoints.

**Rationale:** DRF throttling integrates cleanly with the existing DRF setup, uses the cache backend (configurable), and produces 429 responses with `Retry-After` out of the box. `django-ratelimit` is an additional dependency with overlap.

**Alternative considered:** `django-ratelimit`. Rejected to minimize external dependencies.

---

### D5: Spring Boot Layering Enforcement
**Decision:** Enforce by code review convention and architecture tests (ArchUnit) if the project has it; otherwise enforce via PR review. No new framework introduced.

**Rationale:** The layering rule is architectural, not a runtime concern. ArchUnit can enforce it in tests, but introducing it is optional given the small team size. The primary enforcement is test coverage: controllers with no business logic will have trivial unit tests; services will have rich ones.

---

### D6: Refresh Token Storage — dedicated table
**Decision:** Add a `refresh_tokens` table with columns: `id`, `user_id` (FK), `token_hash` (SHA-256 of the token), `family_id` (UUID grouping a token lineage), `created_at`, `expires_at`, `revoked` (boolean).

**Rationale:** Storing a hash instead of the raw token prevents token leakage if the database is compromised. `family_id` enables token family revocation: all tokens sharing a `family_id` can be revoked atomically when reuse is detected. The `revoked` flag allows soft-delete for audit purposes; a cleanup job can hard-delete old revoked tokens.

**Alternative considered:** Redis-based token store. Rejected because it adds infrastructure complexity and the requirement specifies database storage.

---

### D7: Spring Boot Global Exception Handler — `@RestControllerAdvice`
**Decision:** Single `GlobalExceptionHandler` class annotated `@RestControllerAdvice` with `@ExceptionHandler` methods for each required type. All return `ResponseEntity<ErrorResponse>` where `ErrorResponse` is a record `{ error, message, timestamp }`.

**Rationale:** `@RestControllerAdvice` is the idiomatic Spring MVC approach. Using a single class keeps all exception-to-response mappings in one place. A dedicated `ErrorResponse` record ensures consistent serialization.

---

### D8: Test Strategy
**Decision:**
- Django: unit tests use `unittest.mock.patch` to mock the auth HTTP client; integration tests use a real PostgreSQL test database (Django's `--keepdb` or Testcontainers) and a `responses` library mock for the auth service.
- Spring Boot: unit tests use Mockito to mock repositories and services; integration tests use H2 in-memory or Testcontainers PostgreSQL with no external service calls.
- Mutation testing: `mutmut` for Django, PIT for Spring Boot. Surviving mutants documented in `mutation-notes.md`.

**Rationale:** Aligns with the project TDD policy. Fakes/mocks are preferred for unit tests; real databases for integration tests. `responses` is a lightweight HTTP mock library for Python that intercepts `requests` calls without modifying production code.

## Risks / Trade-offs

- **[Risk] Service layer extraction breaks existing view tests** → Mitigation: Write service-layer unit tests first (TDD), then refactor views to delegate; existing view tests will need updating but will not lose coverage.
- **[Risk] `select_related`/`prefetch_related` additions change query semantics** → Mitigation: Run existing integration tests against a real DB after each ORM change; use `assertNumQueries` to catch regressions.
- **[Risk] Token family revocation is a broad action that may surprise users** → Mitigation: Documented behavior; logout immediately on 401 from reuse detection on the client side (out of scope for this refactor).
- **[Risk] Mutation score targets (≥ 95%) are aggressive and may require extensive test additions** → Mitigation: Run mutation testing early per-module, not at the end; fix as you go.
- **[Risk] DRF throttle rates rely on cache backend** → Mitigation: Configure a cache backend (LocMemCache for tests, Redis/memcached for production) as part of this refactor; document in env-config spec.

## Migration Plan

1. **Spring Boot**: Add `refresh_tokens` table via Flyway/Liquibase migration (or JPA `ddl-auto: update` in dev, explicit migration in prod).
2. **Django**: No schema changes required; service layer, middleware, pagination, filtering, and rate limiting are all application-level changes.
3. **Rollback**: Spring Boot — drop the `refresh_tokens` table and revert the migration. Django — revert middleware and view changes; no data at risk.

## Open Questions

- Should the `family_id` concept be exposed in API error messages, or kept internal? (Current assumption: internal only.)
- Should `mutation-notes.md` live at the repo root or alongside each service's test suite? (Current assumption: one file per service, co-located with tests.)
