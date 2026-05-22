# Requirements: Spring Boot Authentication Microservice

## Purpose
Extract token issuance and credential validation from Django into a dedicated Spring Boot service. Django stops issuing JWTs entirely; clients authenticate directly against this service. This establishes a clean microservices boundary and demonstrates real-world responsibility separation.

## Scope
- **In scope:**
  - Spring Boot project scaffolding (Java 17, Maven)
  - Shared PostgreSQL database, `users` table — only columns `email`, `password_hash`, `role`
  - User registration and login endpoints
  - JWT access token issuance (HMAC-SHA256, 24-hour expiry)
  - Refresh token issuance and rotation (7-day expiry, stored in DB)
  - Token validation endpoint consumed by Django to protect its own routes
  - Roles: `ADMIN`, `ORGANIZER`, `PLAYER`
  - Password hashing: bcrypt (no PBKDF2 compatibility required — no existing users)
  - Service runs on port `8080`

- **Out of scope:**
  - OAuth2 / OpenID Connect flows
  - Social login (Google, GitHub, etc.)
  - Email verification or password reset flows
  - Rate limiting or brute-force protection
  - Any Django code changes (Django migration is a separate task)
  - RSA key management or key rotation
  - User profile data beyond `email`, `password_hash`, `role`

## Requirements

1. The project is generated via [start.spring.io](https://start.spring.io) with Java 17, Maven, and the following dependencies: Spring Web, Spring Security, Spring Data JPA, PostgreSQL Driver.

2. The service connects to the existing PostgreSQL database. The `users` table must contain exactly: `id` (UUID, PK), `email` (VARCHAR, unique, not null), `password_hash` (VARCHAR, not null), `role` (VARCHAR, not null, values: `ADMIN`, `ORGANIZER`, `PLAYER`).

3. Passwords are stored using bcrypt with a cost factor of 12.

4. JWTs are signed with HMAC-SHA256. The signing secret is provided via the environment variable `JWT_SECRET` (minimum 256-bit / 32-character string). The service must refuse to start if `JWT_SECRET` is not set.

5. Access tokens expire exactly 24 hours after issuance. The JWT payload must include: `sub` (user email), `role`, `iat`, `exp`.

6. Refresh tokens are random UUIDs stored in the `refresh_tokens` table (`id`, `user_id` FK, `token`, `expires_at`, `revoked`). Refresh tokens expire 7 days after issuance.

7. `POST /auth/register` creates a new user. Returns `201 Created` on success. Returns `409 Conflict` if the email already exists. Returns `400 Bad Request` if any field is missing or `role` is not one of the allowed values.

8. `POST /auth/login` verifies the email/password pair. Returns `200 OK` with `{ "access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 86400 }`. Returns `401 Unauthorized` for invalid credentials. Returns `400 Bad Request` if any field is missing.

9. `POST /auth/refresh` accepts `{ "refresh_token": "..." }`. Returns a new access token and a new refresh token (old token is revoked). Returns `401 Unauthorized` if the token is expired, revoked, or not found.

10. `POST /auth/validate` accepts `{ "token": "..." }` in the request body. Returns `200 OK` with `{ "valid": true, "email": "...", "role": "..." }` for a valid, non-expired token. Returns `200 OK` with `{ "valid": false }` for an invalid or expired token. This endpoint does not require the caller to be authenticated.

11. All error responses follow the structure: `{ "error": "<machine-readable code>", "message": "<human-readable description>" }`.

12. The service port is configurable via `SERVER_PORT` environment variable, defaulting to `8080`.

## Scenarios

### Successful Registration
- GIVEN a `POST /auth/register` request with body `{ "email": "player@example.com", "password": "StrongPass1!", "role": "PLAYER" }`
- WHEN the email does not already exist in the `users` table
- THEN the service returns `201 Created` with `{ "id": "<uuid>", "email": "player@example.com", "role": "PLAYER" }` and stores a bcrypt hash in `password_hash`

### Duplicate Email on Registration
- GIVEN a `POST /auth/register` request with an email that already exists in the `users` table
- WHEN the request is processed
- THEN the service returns `409 Conflict` with `{ "error": "EMAIL_ALREADY_EXISTS", "message": "An account with this email already exists." }`

### Successful Login
- GIVEN a registered user with email `player@example.com` and a known bcrypt-hashed password
- WHEN `POST /auth/login` is called with the correct credentials
- THEN the service returns `200 OK` with a JWT access token (exp = iat + 86400 seconds) and a refresh token UUID

### Invalid Login Credentials
- GIVEN `POST /auth/login` is called with a valid email but incorrect password
- WHEN the service processes the request
- THEN the service returns `401 Unauthorized` with `{ "error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect." }` and does NOT indicate which field is wrong

### Token Validation — Valid Token
- GIVEN a valid, non-expired JWT issued by this service
- WHEN `POST /auth/validate` is called with that token
- THEN the service returns `200 OK` with `{ "valid": true, "email": "player@example.com", "role": "PLAYER" }`

### Token Validation — Expired Token
- GIVEN a JWT whose `exp` claim is in the past
- WHEN `POST /auth/validate` is called with that token
- THEN the service returns `200 OK` with `{ "valid": false }`

### Refresh Token Rotation
- GIVEN a valid, non-expired refresh token stored in the `refresh_tokens` table
- WHEN `POST /auth/refresh` is called with that token
- THEN the service returns `200 OK` with a new access token and a new refresh token, and the old refresh token row is marked `revoked = true`

### Refresh Token Reuse (Revoked)
- GIVEN a refresh token that has already been revoked
- WHEN `POST /auth/refresh` is called with that token
- THEN the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

### Missing JWT Secret at Startup
- GIVEN the environment variable `JWT_SECRET` is not set
- WHEN the Spring Boot application starts
- THEN the application exits immediately with a non-zero status code and logs `FATAL: JWT_SECRET environment variable is required`

## Open Questions

- **Shared DB ownership:** The `users` table is currently managed by Django migrations. Who owns schema migrations going forward — Django, Spring Boot (Flyway/Liquibase), or a separate migration tool? This must be resolved before the service writes to the `users` table in a shared environment.
