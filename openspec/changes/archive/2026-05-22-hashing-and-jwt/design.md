## Context

The `auth-service` currently issues JWTs with a 24-hour expiry and has no logout mechanism. This change makes two focused modifications: shortening the access token lifetime to 15 minutes (a single property change + test updates) and adding `POST /auth/logout` to enable explicit refresh token revocation. The `refresh_tokens` table already has a `revoked` column; no schema migration is required.

## Goals / Non-Goals

**Goals:**
- Reduce access token exposure window from 24 h to 15 min
- Give clients a way to explicitly end a session by revoking a specific refresh token
- Keep the change minimal — touch only what is necessary

**Non-Goals:**
- Access token blocklisting (access tokens remain valid for up to 15 min after logout)
- Sign-out-everywhere (only the presented refresh token is revoked)
- Any changes to the Django side or the `/auth/validate` contract

## Decisions

### D1: 15-minute access token with no blocklist
**Decision**: Access tokens expire in 900 seconds. No server-side revocation of access tokens is implemented.  
**Rationale**: A 15-minute window is the industry standard short-lived token pattern. Implementing a blocklist would require a shared cache (Redis or DB lookup on every request), adding infrastructure complexity that is out of scope. Clients that need immediate invalidation use `/auth/logout` to revoke the refresh token, preventing new access tokens from being issued.  
**Trade-off**: A stolen access token remains usable for up to 15 minutes. Acceptable given the learning stage of this project.

### D2: Logout revokes one token, not all user tokens
**Decision**: `POST /auth/logout` accepts a single refresh token UUID and revokes only that row.  
**Rationale**: Matches the stated requirement. Single-token revocation is the correct default; sign-out-everywhere can be added later as a separate capability if needed.  
**Alternative considered**: Revoke all tokens by `user_id` — rejected because it would log out all devices simultaneously, which is a distinct UX behavior not requested here.

### D3: Logout returns 204, not 200
**Decision**: Successful logout returns `204 No Content` with no response body.  
**Rationale**: REST convention for a successful mutation that produces no content to return. Avoids any question of what to return in the body.

### D4: Logout rejects already-revoked and expired tokens with 401
**Decision**: Attempting to logout with a token that is already revoked, expired, or unknown returns `401 Unauthorized`.  
**Rationale**: Consistent with the error contract used by `/auth/refresh`. Makes replay attacks immediately visible.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Clients using 24 h tokens will have shorter sessions after this change | Clients must implement refresh logic — documented as a breaking change in `expires_in` |
| 15 min token + network latency could cause edge-case expiry on slow clients | Clock skew is inherent to JWT; clients should refresh before expiry using `expires_in` |
| Tests hardcoding `86400` will fail after the property change | All such tests are updated in the same task group as the property change |

## Migration Plan

1. Update `jwt.access-token-expiration-seconds=900` in `application.properties`
2. Update `expires_in` hardcoded value in `RefreshTokenService.rotate()` from `86400` to use the configured value
3. Add `logout()` method to `RefreshTokenService`
4. Add `POST /auth/logout` to `AuthController` and permit it in `SecurityConfig`
5. Update all test assertions from `86400` to `900`
6. Add logout tests
7. Run `mvn test` — all tests must pass
