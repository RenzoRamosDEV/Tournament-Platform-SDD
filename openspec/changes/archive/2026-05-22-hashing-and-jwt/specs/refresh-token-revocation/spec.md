## ADDED Requirements

### Requirement: Explicit refresh token revocation via logout
The auth service SHALL expose `POST /auth/logout` which accepts `{ "refresh_token": "<uuid>" }` and marks the matching row in `refresh_tokens` as `revoked = true`. This endpoint MUST NOT require an `Authorization` header. On success it MUST return `204 No Content` with no response body. If the token is not found, already revoked, or expired, the service MUST return `401 Unauthorized` with the standard error body. After logout, the revoked token MUST be rejected by `POST /auth/refresh`.

#### Scenario: Successful logout
- **WHEN** `POST /auth/logout` is called with a valid, non-revoked, non-expired refresh token
- **THEN** the service returns `204 No Content` and the `refresh_tokens` row has `revoked = true`

#### Scenario: Logout prevents subsequent refresh
- **WHEN** `POST /auth/logout` has returned `204` for a token, and `POST /auth/refresh` is then called with the same token
- **THEN** `POST /auth/refresh` returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

#### Scenario: Logout with unknown token
- **WHEN** `POST /auth/logout` is called with a UUID that does not exist in `refresh_tokens`
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

#### Scenario: Logout with already-revoked token
- **WHEN** `POST /auth/logout` is called with a refresh token where `revoked = true`
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or has been revoked." }`

#### Scenario: Logout without Authorization header
- **WHEN** `POST /auth/logout` is called with no `Authorization` header but a valid refresh token body
- **THEN** the service processes the request and returns `204 No Content`
