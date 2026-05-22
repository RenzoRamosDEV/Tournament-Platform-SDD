## ADDED Requirements

### Requirement: Access token issuance
Upon successful login, the auth service SHALL issue a JWT signed with HMAC-SHA256 using the value of the `JWT_SECRET` environment variable. The token payload MUST include `sub` (user email), `role`, `iat` (issued-at epoch seconds), and `exp` (iat + 900 seconds). The service MUST refuse to start if `JWT_SECRET` is not set or is shorter than 32 characters.

#### Scenario: JWT payload structure
- **WHEN** a user logs in successfully
- **THEN** the issued JWT contains claims `sub` (email), `role`, `iat`, and `exp` where `exp = iat + 900`

#### Scenario: Missing JWT_SECRET at startup
- **WHEN** the application starts without the `JWT_SECRET` environment variable set
- **THEN** the application exits immediately with a non-zero status code and logs `FATAL: JWT_SECRET environment variable is required`

#### Scenario: JWT_SECRET too short at startup
- **WHEN** the application starts with `JWT_SECRET` shorter than 32 characters
- **THEN** the application exits immediately with a non-zero status code and logs `FATAL: JWT_SECRET must be at least 32 characters`

#### Scenario: expires_in reflects 15-minute expiry
- **WHEN** a user logs in or refreshes successfully
- **THEN** the response body contains `"expires_in": 900`

### Requirement: Refresh token issuance and rotation
Upon successful login, the auth service SHALL generate a random UUID refresh token, store it in the `refresh_tokens` table with `expires_at = now + 7 days` and `revoked = false`, and return it alongside the access token. `POST /auth/refresh` MUST atomically revoke the presented refresh token and issue a new access token and refresh token pair.

#### Scenario: Refresh token issued on login
- **WHEN** a user logs in successfully
- **THEN** a new row is inserted into `refresh_tokens` with the user's `id`, a UUID token, `expires_at = now + 7 days`, and `revoked = false`

#### Scenario: Successful token refresh
- **WHEN** `POST /auth/refresh` is called with a valid, non-expired, non-revoked refresh token
- **THEN** the service returns `200 OK` with a new access token and a new refresh token UUID, and the old refresh token row is updated to `revoked = true`

#### Scenario: Revoked refresh token reuse
- **WHEN** `POST /auth/refresh` is called with a refresh token where `revoked = true`
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

#### Scenario: Expired refresh token
- **WHEN** `POST /auth/refresh` is called with a refresh token where `expires_at` is in the past
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

#### Scenario: Unknown refresh token
- **WHEN** `POST /auth/refresh` is called with a UUID that does not exist in `refresh_tokens`
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`
