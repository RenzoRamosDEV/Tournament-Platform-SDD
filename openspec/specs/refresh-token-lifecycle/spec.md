## ADDED Requirements

### Requirement: Refresh token issuance on login
When a user successfully logs in via `POST /auth/login`, the auth service SHALL issue a refresh token and persist it in the `refresh_tokens` table with: `user_id`, `token_hash` (SHA-256 of the raw token), `family_id` (a new UUID for this token lineage), `created_at`, `expires_at` (configurable, default 7 days), `revoked = false`. The raw refresh token value MUST be returned to the client; only its hash is stored.

#### Scenario: Login persists refresh token record
- **WHEN** `POST /auth/login` succeeds with valid credentials
- **THEN** a new row is inserted in `refresh_tokens` with `revoked = false` and `expires_at` set to the configured expiry; the raw token is returned to the client

#### Scenario: Hashed token is stored, not raw
- **WHEN** a refresh token is issued
- **THEN** the `token_hash` column contains the SHA-256 hash of the raw token; the raw value is not stored anywhere in the database

### Requirement: Atomic refresh token rotation
When `POST /auth/refresh` is called with a valid refresh token, the service MUST atomically: (1) revoke (delete or mark `revoked = true`) the old refresh token, and (2) issue and persist a new refresh token within the same database transaction. The new refresh token MUST share the same `family_id` as the old one. The response MUST include both a new access token and the new refresh token.

#### Scenario: Refresh rotates token atomically
- **WHEN** `POST /auth/refresh` is called with a valid, non-revoked, non-expired refresh token
- **THEN** the old token row has `revoked = true` (or is deleted) and a new row with the same `family_id` and `revoked = false` is inserted in the same transaction; the response contains a new access token and new refresh token

#### Scenario: Expired refresh token rejected
- **WHEN** `POST /auth/refresh` is called with a refresh token whose `expires_at` is in the past
- **THEN** the service returns `HTTP 401` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

### Requirement: Token family revocation on reuse detection
If `POST /auth/refresh` is called with a refresh token that is already marked `revoked = true` (indicating reuse of a previously rotated token), the service MUST: (1) return `HTTP 401`, and (2) revoke ALL tokens sharing the same `family_id` (token family revocation), forcing the user to log in again.

#### Scenario: Reuse of revoked token triggers family revocation
- **WHEN** a user receives RT-1 on login, refreshes to get RT-2 (RT-1 is revoked), and then sends RT-1 again to `/auth/refresh`
- **THEN** the service returns `HTTP 401`, and ALL tokens in the RT-1/RT-2 family (including RT-2) are revoked; any subsequent use of RT-2 also returns `HTTP 401`

#### Scenario: Reuse detection error body
- **WHEN** token family revocation is triggered
- **THEN** the response is `HTTP 401` with body `{ "error": "REFRESH_TOKEN_REUSE_DETECTED", "message": "Security violation detected. Please log in again." }`

### Requirement: Expired tokens rejected with 401
Refresh tokens past their `expires_at` timestamp MUST be rejected. The service MUST return `HTTP 401` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`.

#### Scenario: Expired token rejected
- **WHEN** `POST /auth/refresh` is called with a token where `expires_at < now()`
- **THEN** the service returns `HTTP 401` with `{ "error": "INVALID_REFRESH_TOKEN" }`
