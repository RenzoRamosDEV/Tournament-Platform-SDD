# Requirements: Global Refactor — Production-Ready Backend & Auth Service

## Purpose
Both the Django+DRF tournament backend and the Spring Boot auth service were built incrementally and carry structural debt: business logic mixed into views, unguarded N+1 queries, fragile auth middleware with no fault tolerance, and insufficient test isolation. This refactor elevates both services to a production-ready standard by enforcing clear layered architecture, measurable performance guards, resilient inter-service communication, and a fully autonomous test suite for each service.

## Scope

- **In scope:**
  - Django+DRF: view/serializer/service layer separation, N+1 ORM query elimination, auth middleware hardening, global pagination, query filtering, and rate limiting
  - Spring Boot: layered architecture (Controller/Service/Repository), security filter chain configuration, refresh token lifecycle (issuance, rotation, revocation), and centralized exception handling
  - Testing strategy for both services: unit tests with mocks/fakes, integration tests, and mutation testing targets per the existing TDD policy
- **Out of scope:**
  - Adding new business features (e.g., new tournament types, new ELO formulas)
  - Changing the database schema beyond what is strictly required for refresh token storage
  - Frontend or mobile client changes
  - Infrastructure provisioning, CI/CD pipeline setup, or deployment configuration
  - Third-party authentication providers (OAuth2, SSO)

---

## Requirements

### Django + DRF Backend

1. All business logic (match result reporting, ELO calculation, tournament state transitions) MUST reside in a dedicated service layer (`services.py` or equivalent module), completely decoupled from views and serializers. Views MUST only call service methods and delegate HTTP response formatting.

2. All list endpoints that traverse foreign-key or many-to-many relations (users ↔ teams, teams ↔ tournaments, tournaments ↔ matches) MUST use `select_related` or `prefetch_related` to eliminate N+1 queries. The number of SQL queries issued per list request MUST NOT grow with the number of returned objects (i.e., O(1) queries with respect to result count).

3. The JWT authentication middleware that communicates with the Java auth service MUST:
   - Set a hard timeout of **2 seconds** on the outbound HTTP call.
   - Return HTTP `503 Service Unavailable` with a standard JSON error body if the auth service is unreachable, times out, or returns a 5xx response.
   - Return HTTP `401 Unauthorized` with a standard JSON error body if the token is invalid or rejected by the auth service.
   - MUST NOT raise unhandled exceptions that propagate to Django's default error handler.

4. All list endpoints MUST enforce global pagination with a default page size of **20 items** and a maximum of **100 items** per page. Clients MUST be able to override page size via a `page_size` query parameter up to the maximum.

5. Critical endpoints (at minimum: login proxy, token refresh proxy, match result submission) MUST enforce rate limiting: **5 requests/minute** for unauthenticated requests and **60 requests/minute** for authenticated requests per IP. Requests exceeding the limit MUST receive HTTP `429 Too Many Requests`.

6. All list endpoints that expose filterable resources (tournaments, matches, users) MUST support query filtering via URL parameters on at minimum: `status`, `date_range`, and `owner/creator id` where applicable.

### Spring Boot Auth Service

7. The project MUST follow a strict three-layer structure: Controllers handle HTTP binding and delegation only; Services contain all business logic; Repositories are the sole data-access point. No business logic is permitted in Controllers or Repositories.

8. The Spring Security filter chain MUST:
   - Allow unauthenticated access to `/auth/login`, `/auth/register`, and `/auth/refresh` endpoints.
   - Require authentication on all internal token validation endpoints (e.g., `/auth/validate`).
   - Return structured JSON error bodies (not HTML) for `401` and `403` responses.

9. Refresh tokens MUST be stored in the database with the following lifecycle:
   - On login: a new refresh token is issued and persisted with an expiry timestamp.
   - On refresh: the old refresh token is revoked (deleted or marked invalid) and a new one is issued atomically. Reuse of a previously revoked refresh token MUST return HTTP `401` and invalidate all tokens for that user (token family revocation).
   - On logout: the refresh token for the session is immediately revoked.
   - Expired refresh tokens MUST be rejected with HTTP `401`.

10. A `@RestControllerAdvice` global exception handler MUST translate all thrown exceptions into a uniform JSON structure: `{ "error": "<code>", "message": "<human-readable>", "timestamp": "<ISO-8601>" }`. Covered exception types MUST include: `AuthenticationException`, `JwtException`, `ConstraintViolationException`, `MethodArgumentNotValidException`, `EntityNotFoundException`, and unhandled `Exception` (500 fallback).

### Testing

11. Django unit tests for service-layer logic MUST mock the auth service HTTP client. No Django unit test MUST require the Java service to be running. The mock MUST cover: successful validation, timeout, 5xx error, and 401/403 responses from the auth service.

12. Spring Boot unit tests for service-layer logic MUST use mocked repositories (Mockito or equivalent). No Spring Boot unit test MUST require a live database connection.

13. Both services MUST achieve a minimum of **90% line coverage** as measured by their respective coverage tools (coverage.py for Django, JaCoCo for Spring Boot).

14. Both services MUST achieve a mutation score of **≥ 95%** as required by the project TDD policy. Any surviving mutant MUST be documented with a justification in a `mutation-notes.md` file alongside the test suite.

15. Integration tests for Django MUST use a real PostgreSQL instance (via test database or Testcontainers) and a mocked/fake auth service (not the live Java service).

16. Integration tests for Spring Boot MUST use an embedded H2 database or Testcontainers PostgreSQL, and MUST NOT call any external service.

---

## Scenarios

### Django Auth Middleware — Auth Service Timeout
- GIVEN a valid incoming HTTP request with a Bearer token
- WHEN the Django middleware calls the Java auth service and no response is received within 2 seconds
- THEN the middleware returns HTTP 503 with body `{"error": "auth_service_unavailable", "message": "Authentication service is temporarily unavailable"}` and the request is not forwarded to the view

### Django Auth Middleware — Invalid Token
- GIVEN a request with a malformed or expired JWT
- WHEN the middleware calls the Java auth service and receives HTTP 401
- THEN the middleware returns HTTP 401 with body `{"error": "invalid_token", "message": "Token is invalid or expired"}` and no view logic is executed

### Django List Endpoint — N+1 Guard
- GIVEN a tournament list endpoint with 50 tournaments each linked to 10 teams
- WHEN the endpoint is called
- THEN the total number of database queries is constant (does not scale with tournament or team count), verified by Django's query count assertions in tests

### Django Rate Limiting — Unauthenticated Burst
- GIVEN an unauthenticated client sending requests to the login endpoint
- WHEN 6 or more requests are sent within a 60-second window
- THEN the 6th and subsequent requests receive HTTP 429 with a `Retry-After` header

### Spring Boot Refresh Token Reuse Detection
- GIVEN a user has logged in and received refresh token RT-1
- WHEN the user refreshes once (RT-1 is revoked, RT-2 is issued) and then attempts to use RT-1 again
- THEN the server returns HTTP 401, revokes RT-2 and all active tokens for that user, and the user must log in again

### Spring Boot Global Exception Handler — Validation Error
- GIVEN a client submits a registration request with a missing required field
- WHEN Spring's validation layer throws `MethodArgumentNotValidException`
- THEN the response is HTTP 400 with body `{"error": "validation_error", "message": "<field-level detail>", "timestamp": "<ISO-8601>"}`

### Spring Boot Logout
- GIVEN an authenticated user with an active refresh token in the database
- WHEN the user calls the logout endpoint
- THEN the refresh token record is deleted or marked revoked, and any subsequent use of that token returns HTTP 401
