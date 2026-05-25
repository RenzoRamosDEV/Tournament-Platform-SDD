## 1. Django — Service Layer Extraction

- [x] 1.1 Create `services.py` in the `matches` app; move match result reporting and ELO update logic out of the view into `MatchService.report_result()`
- [x] 1.2 Create `services.py` in the `tournaments` app; move tournament state transition logic into `TournamentService.start()` and related methods
- [x] 1.3 Create `services.py` in the `users` app (if any business logic exists in user views); move it out
- [x] 1.4 Refactor all view/ViewSet action methods to be thin delegators: extract input → call service → return response
- [x] 1.5 Write unit tests for `MatchService` covering: successful result report, ELO update triggered, invalid state transitions
- [x] 1.6 Write unit tests for `TournamentService` covering: successful start, invalid state, non-existent tournament
- [x] 1.7 Confirm no business logic remains in any ViewSet action or serializer (code review / grep)

## 2. Django — N+1 Query Elimination

- [x] 2.1 Add `select_related("tournament")` and `prefetch_related("teams")` to `MatchViewSet.get_queryset()`
- [x] 2.2 Add `prefetch_related("teams")` to `TournamentViewSet.get_queryset()`
- [x] 2.3 Add `prefetch_related("tournaments", "members")` to `TeamViewSet.get_queryset()`
- [x] 2.4 Add `prefetch_related("teams")` to `UserViewSet.get_queryset()` (if user list endpoint accesses teams)
- [x] 2.5 Write `assertNumQueries` integration tests for each list endpoint verifying constant query count regardless of result set size
- [ ] 2.6 Run the full test suite against a real PostgreSQL instance to confirm no regressions

## 3. Django — JWT Middleware Hardening

- [x] 3.1 Add catch-all `except Exception` block to the middleware's outbound HTTP call; ensure it returns `JsonResponse({"error": "AUTH_SERVICE_UNAVAILABLE", ...}, status=503)` and never re-raises
- [x] 3.2 Verify the `requests` call includes `timeout=2` (already specified in existing spec; confirm implementation matches)
- [x] 3.3 Write unit test: unexpected exception (e.g., `OSError`) is caught and returns 503
- [x] 3.4 Write unit test: all exception paths confirm Django's 500 handler is never reached

## 4. Django — Global Pagination

- [x] 4.1 Set `MAX_PAGE_SIZE = 100` and `page_size_query_param = "page_size"` on the global `PageNumberPagination` class in `settings.py`
- [x] 4.2 Write tests verifying: default page size 20, `page_size=50` override works, `page_size=200` is clamped to 100

## 5. Django — Rate Limiting

- [x] 5.1 Configure `DEFAULT_THROTTLE_CLASSES` in `REST_FRAMEWORK` settings with `AnonRateThrottle` (5/min) and `UserRateThrottle` (60/min)
- [x] 5.2 Configure `DEFAULT_THROTTLE_RATES` with `anon: "5/min"` and `user: "60/min"`
- [x] 5.3 Apply throttle classes explicitly to login proxy, refresh proxy, and match result submission views (per-view override if different from global)
- [x] 5.4 Configure cache backend for throttle storage (LocMemCache for tests, document Redis for production)
- [x] 5.5 Write tests verifying: 6th unauthenticated request to login returns 429 with `Retry-After`, authenticated requests succeed up to 60/min

## 6. Django — Query Filtering Extensions

- [x] 6.1 Add `date_from` and `date_to` filter fields to `TournamentFilterSet` with date validation (ISO-8601, 400 on invalid)
- [x] 6.2 Add `created_by` filter field to `TournamentFilterSet` (integer FK, 200 empty list on non-existent user)
- [x] 6.3 Add `date_from` and `date_to` filter fields to `MatchFilterSet` with date validation
- [x] 6.4 Write tests for all new filter fields: valid date range returns filtered results, invalid date format returns 400, non-existent `created_by` returns empty list

## 7. Spring Boot — Layered Architecture Enforcement

- [x] 7.1 Audit all `@RestController` classes: move any business logic found into the corresponding `@Service`
- [x] 7.2 Audit all `@Repository` interfaces: remove any computed behavior or business logic found
- [x] 7.3 Verify no `@Controller` class imports a `@Repository` interface directly
- [x] 7.4 Write or update service unit tests (Mockito) covering all business logic methods in `AuthService`, `UserService`, `TokenService`

## 8. Spring Boot — Security Filter Chain

- [x] 8.1 Create or update `SecurityConfig` with a `SecurityFilterChain` bean permitting unauthenticated access to `/auth/login`, `/auth/register`, `/auth/refresh`
- [x] 8.2 Require authentication on all other endpoints (including `/auth/validate`, `/auth/logout`)
- [x] 8.3 Disable CSRF for stateless JWT auth
- [x] 8.4 Configure `AuthenticationEntryPoint` to return JSON 401 (not HTML) using the global error structure
- [x] 8.5 Configure `AccessDeniedHandler` to return JSON 403 (not HTML) using the global error structure
- [x] 8.6 Write tests: unauthenticated access to `/auth/login` returns 200, unauthenticated access to `/auth/validate` returns JSON 401

## 9. Spring Boot — Refresh Token Lifecycle

- [x] 9.1 Create `RefreshToken` JPA entity with fields: `id`, `userId`, `tokenHash`, `familyId`, `createdAt`, `expiresAt`, `revoked`
- [x] 9.2 Create `RefreshTokenRepository` with JPA methods: `findByTokenHash`, `findAllByFamilyId`, `deleteByExpiresAtBefore`
- [x] 9.3 Implement `TokenService.issueRefreshToken(userId)`: generate UUID token, hash it (SHA-256), persist, return raw token
- [x] 9.4 Implement `TokenService.rotateRefreshToken(rawToken)`: verify not revoked/expired, revoke old, issue new (same `familyId`), return new tokens atomically in a `@Transactional` method
- [x] 9.5 Implement reuse detection in `rotateRefreshToken`: if token is already revoked, call `revokeFamily(familyId)` and throw exception returning 401
- [x] 9.6 Wire `issueRefreshToken` into `AuthService.login()` response
- [x] 9.7 Wire `rotateRefreshToken` into `POST /auth/refresh` controller → service call
- [x] 9.8 Write unit tests (Mockito): login issues token, rotation atomically revokes old and issues new, reuse detection triggers family revocation, expired token rejected
- [x] 9.9 Write integration test (H2 or Testcontainers): end-to-end RT-1 → refresh → RT-2 → reuse RT-1 → 401 + RT-2 revoked

## 10. Spring Boot — Global Exception Handler

- [x] 10.1 Create `GlobalExceptionHandler` class annotated `@RestControllerAdvice`
- [x] 10.2 Create `ErrorResponse` record: `String error`, `String message`, `String timestamp` (ISO-8601)
- [x] 10.3 Add `@ExceptionHandler(AuthenticationException.class)` → 401 JSON
- [x] 10.4 Add `@ExceptionHandler(JwtException.class)` → 401 JSON
- [x] 10.5 Add `@ExceptionHandler(MethodArgumentNotValidException.class)` → 400 JSON with field-level detail
- [x] 10.6 Add `@ExceptionHandler(ConstraintViolationException.class)` → 400 JSON
- [x] 10.7 Add `@ExceptionHandler(EntityNotFoundException.class)` → 404 JSON
- [x] 10.8 Add `@ExceptionHandler(Exception.class)` → 500 JSON (no stack trace in body)
- [x] 10.9 Write unit/integration tests for each handler: verify status code, `Content-Type: application/json`, and body structure

## 11. Testing — Coverage and Mutation Targets

- [ ] 11.1 Run `coverage run manage.py test` and `coverage report` for Django; fix coverage gaps until ≥ 90%
- [ ] 11.2 Configure JaCoCo in Spring Boot build; run tests and verify ≥ 90% line coverage
- [ ] 11.3 Run `mutmut run` on Django service; document any surviving mutants in `django-api/mutation-notes.md` until score ≥ 95%
- [ ] 11.4 Run PIT on Spring Boot service; document any surviving mutants in `auth-service/mutation-notes.md` until score ≥ 95%
- [ ] 11.5 Create `django-api/mutation-notes.md` and `auth-service/mutation-notes.md` (even if empty, to satisfy the requirement)
