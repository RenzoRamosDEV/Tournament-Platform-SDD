## MODIFIED Requirements

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
