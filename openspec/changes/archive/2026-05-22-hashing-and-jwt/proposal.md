## Why

The auth-service currently issues access tokens with a 24-hour expiry, and there is no way for a client to explicitly invalidate a session. Shortening the access token lifetime to 15 minutes reduces the window of exposure if a token is stolen, and adding a `/auth/logout` endpoint gives clients a clean way to revoke a refresh token on demand.

## What Changes

- `jwt.access-token-expiration-seconds` is reduced from `86400` to `900` (15 min)
- All `LoginResponse` payloads return `"expires_in": 900` instead of `86400`
- `POST /auth/logout` is added: accepts `{ "refresh_token": "<uuid>" }`, marks the token `revoked = true`, returns `204 No Content`
- Existing tests asserting `expires_in = 86400` are updated to `900`
- No schema migrations are needed (the `refresh_tokens.revoked` column already exists)

## Capabilities

### New Capabilities
- `refresh-token-revocation`: Explicit client-initiated revocation of a single refresh token via `POST /auth/logout`

### Modified Capabilities
- `jwt-token-issuance`: Access token expiry changes from 24 h (86400 s) to 15 min (900 s); `expires_in` in all token responses updated accordingly

## Impact

- **`auth-service/src/main/resources/application.properties`**: `jwt.access-token-expiration-seconds` value changed to `900`
- **`auth-service/src/main/resources/application-test.properties`**: no change needed (tests use the property value)
- **`AuthController`**: new `POST /auth/logout` handler added
- **`RefreshTokenService`**: new `logout(UUID token)` method
- **`SecurityConfig`**: `/auth/logout` added to the permitted paths
- **Test files**: all assertions on `expires_in = 86400` updated to `900`; new logout tests added
- **Django**: not modified — `/auth/validate` contract is unchanged
