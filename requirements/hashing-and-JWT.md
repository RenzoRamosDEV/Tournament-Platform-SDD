# Requirements: Auth Service — Hashing, JWT Expiry & Logout

## Purpose
Update the existing Spring Boot `auth-service` to tighten token security and add a proper logout flow. The access token expiry is shortened from 24 hours to 15 minutes (limiting the blast radius of a stolen token), and `POST /auth/logout` is added to allow clients to explicitly revoke a refresh token without needing to wait for it to expire naturally.

## Scope
- **In scope:**
  - Change JWT access token expiry from 86400 seconds (24 h) to 900 seconds (15 minutes)
  - Add `POST /auth/logout` endpoint that accepts a refresh token and marks it `revoked = true` in the `refresh_tokens` table
  - Update the `jwt.access-token-expiration-seconds` property value and the `expires_in` field in `LoginResponse` to reflect 900
  - BCryptPasswordEncoder strength 12 is already in place — confirm it is not changed

- **Out of scope:**
  - Revoking all refresh tokens for a user (sign-out-everywhere)
  - Access token blocklisting or early revocation of access tokens
  - Changes to `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, or `POST /auth/validate` beyond the expiry value change
  - Any Django-side changes
  - Rate limiting or account lockout

## Requirements

1. The JWT access token expiry MUST be exactly 900 seconds (15 minutes) from the time of issuance. The `exp` claim MUST equal `iat + 900`.

2. The `expires_in` field in all `LoginResponse` payloads (login and refresh responses) MUST return `900`, not `86400`.

3. The `jwt.access-token-expiration-seconds` property in `application.properties` MUST be updated to `900`. Tests that assert `expires_in = 86400` MUST be updated to assert `900`.

4. The JWT signing secret MUST continue to be read exclusively from the `JWT_SECRET` environment variable (minimum 32 characters). It MUST NOT be hardcoded anywhere in the codebase.

5. Passwords MUST continue to be hashed with BCryptPasswordEncoder at strength (cost factor) 12. Plain-text passwords MUST never be stored or logged.

6. Refresh tokens MUST expire 7 days after issuance (`expires_at = now + 7 days`). This value is already implemented and MUST NOT change.

7. `POST /auth/logout` MUST accept a JSON body `{ "refresh_token": "<uuid>" }`. This endpoint MUST NOT require an `Authorization` header.

8. `POST /auth/logout` MUST mark the matching refresh token row as `revoked = true` in the `refresh_tokens` table. It MUST return `204 No Content` on success.

9. `POST /auth/logout` MUST return `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }` if the token is not found, already revoked, or expired.

10. `POST /auth/logout` MUST be accessible without authentication (no bearer token required), consistent with the other `/auth/**` endpoints.

11. After a successful logout, calling `POST /auth/refresh` with the same token MUST return `401 Unauthorized` — the revocation MUST be durable.

## Scenarios

### Access Token Expiry Reduced to 15 Minutes
- GIVEN a user logs in successfully
- WHEN the `LoginResponse` is returned
- THEN `expires_in` equals `900` and the JWT `exp` claim equals `iat + 900`

### Successful Logout
- GIVEN a valid, non-revoked refresh token exists in the `refresh_tokens` table
- WHEN `POST /auth/logout` is called with `{ "refresh_token": "<token>" }`
- THEN the service returns `204 No Content` and the token row has `revoked = true`

### Logout Prevents Subsequent Refresh
- GIVEN `POST /auth/logout` has been called with a refresh token and returned `204`
- WHEN `POST /auth/refresh` is called with the same refresh token
- THEN the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN" }`

### Logout with Unknown Token
- GIVEN a UUID that does not exist in the `refresh_tokens` table
- WHEN `POST /auth/logout` is called with that UUID
- THEN the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

### Logout with Already-Revoked Token
- GIVEN a refresh token where `revoked = true`
- WHEN `POST /auth/logout` is called with that token
- THEN the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

### Logout Without Authorization Header
- GIVEN no `Authorization` header is present in the request
- WHEN `POST /auth/logout` is called with a valid refresh token body
- THEN the service processes the request normally and returns `204 No Content`

### JWT Secret Not Hardcoded
- GIVEN the application starts with `JWT_SECRET` set via environment variable
- WHEN tokens are issued
- THEN no JWT secret value appears as a string literal in any `.java`, `.properties`, or `.yaml` source file
