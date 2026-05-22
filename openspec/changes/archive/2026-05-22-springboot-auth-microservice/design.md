## Context

The tournament platform currently runs as a single Django application that owns both domain logic (tournaments, teams, matches) and authentication (JWT issuance via `djangorestframework-simplejwt`). This task extracts auth into a standalone Spring Boot service that shares the existing PostgreSQL database but owns only the identity-related tables. Django is not modified in this task; the integration point is `POST /auth/validate` which Django will use in a follow-up task.

The shared database is a deliberate short-term tradeoff: it avoids data sync complexity while the team learns microservices boundaries. Long-term, the auth service should own its own DB instance.

## Goals / Non-Goals

**Goals:**
- Stand up a Spring Boot service that handles registration, login, JWT issuance, refresh token rotation, and token validation
- Operate independently of Django (no shared code, no service-to-service calls at startup)
- Use the existing `users` table schema without requiring Django migration changes
- Be runnable locally alongside Django via environment variables

**Non-Goals:**
- Changing any Django code in this task
- Implementing rate limiting, account lockout, or email verification
- Producing Docker/Kubernetes deployment configuration
- Full OAuth2 / OIDC compliance
- Migrating existing users or PBKDF2 hashes

## Decisions

### D1: Shared PostgreSQL database (not separate DB)
**Decision**: The auth service connects to the same Postgres instance and `users` table as Django.  
**Rationale**: Avoids data duplication and sync issues at this learning stage. The `users` table already has the fields we need. A separate DB would require a migration pipeline before any auth work can proceed.  
**Alternative considered**: Separate `auth_db` schema in the same instance — adds isolation but complicates connection management without meaningful benefit for a single-developer project.  
**Risk**: Schema coupling. Django and Spring Boot both have opinions about `users`. Mitigated by Spring Boot using Hibernate `validate` mode (never auto-DDL on the `users` table) and Flyway managing only `refresh_tokens`.

### D2: HMAC-SHA256 JWT (shared secret) over RSA
**Decision**: Sign JWTs with HMAC-SHA256 using a shared secret in `JWT_SECRET`.  
**Rationale**: Simpler key management for a learning project. Django can verify tokens locally using the same secret without calling the auth service.  
**Alternative considered**: RSA keypair — better in production (only auth service holds the private key), but requires key distribution and adds operational complexity that obscures the architecture lesson.

### D3: jjwt library for JWT operations
**Decision**: Use `io.jsonwebtoken:jjwt-api` (+ `jjwt-impl`, `jjwt-jackson`) at version 0.12.x.  
**Rationale**: De-facto standard JWT library for Java. Fluent API, well-maintained, Spring-friendly.  
**Alternative considered**: Nimbus JOSE+JWT — more feature-rich but heavier; overkill for HMAC-SHA256 use case.

### D4: Flyway for `refresh_tokens` table only
**Decision**: Use Flyway to manage the `refresh_tokens` table DDL. The `users` table is managed exclusively by Django migrations.  
**Rationale**: Flyway gives us a reproducible migration history for the new table without touching Django-owned schema.  
**Constraint**: Flyway must be configured to ignore the `users` table. Spring Boot's JPA `ddl-auto` is set to `validate` to catch schema drift without modifying tables.

### D5: Stateless `/auth/validate` (no DB lookup)
**Decision**: Token validation is purely cryptographic — no DB round-trip.  
**Rationale**: Keeps validation fast and the auth service out of the hot path for every Django request. Revocation is not required in this task scope.  
**Trade-off**: A stolen access token remains valid until expiry (24h). Acceptable for this learning stage; refresh token revocation is handled at the refresh endpoint.

### D6: Refresh token rotation with immediate revocation
**Decision**: Each `POST /auth/refresh` call revokes the presented token and issues a new one atomically.  
**Rationale**: Rotation limits the damage window if a refresh token is intercepted. If the old token is reused after rotation, the service rejects it immediately.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Schema drift between Django and Spring Boot models for `users` | Hibernate `validate` mode will fail fast at startup if columns are missing or mistyped |
| `JWT_SECRET` leaked in environment | Document minimum 32-char requirement; service refuses to start if unset |
| Refresh token table grows unbounded | Out of scope; a cleanup job is a follow-up task |
| Django and Spring Boot competing on `users` table writes | In this task, Spring Boot only inserts new users; Django still manages existing rows. Coordinate on constraint names to avoid migration conflicts. |

## Migration Plan

1. Run `auth-service` locally with `spring.jpa.hibernate.ddl-auto=validate` and confirm it reads the existing `users` table without error.
2. Flyway applies `V1__create_refresh_tokens.sql` on first startup.
3. Test all four endpoints manually and via integration tests before wiring to Django.
4. Django migration (removing `simplejwt`, calling `/auth/validate`) is a separate follow-up change.

## Open Questions

- **Schema ownership long-term**: When Django is eventually decoupled from the shared DB, who runs the final `users` table migration? This needs a decision before production deployment.
