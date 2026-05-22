## ADDED Requirements

### Requirement: Stateless JWT validation
The auth service SHALL expose `POST /auth/validate` which accepts `{ "token": "<jwt>" }` and verifies the token's HMAC-SHA256 signature and expiry without any database lookup. The endpoint MUST NOT require the caller to be authenticated. A valid token response MUST include the `email` and `role` claims extracted from the JWT payload. An invalid or expired token MUST return `{ "valid": false }` with HTTP `200 OK` — never a `4xx` status — so callers can handle the result as data rather than an error.

#### Scenario: Valid token
- **WHEN** `POST /auth/validate` is called with a well-formed JWT whose signature is valid and `exp` is in the future
- **THEN** the service returns `200 OK` with `{ "valid": true, "email": "<sub claim>", "role": "<role claim>" }`

#### Scenario: Expired token
- **WHEN** `POST /auth/validate` is called with a JWT whose `exp` claim is in the past
- **THEN** the service returns `200 OK` with `{ "valid": false }`

#### Scenario: Tampered signature
- **WHEN** `POST /auth/validate` is called with a JWT whose signature does not match the `JWT_SECRET`
- **THEN** the service returns `200 OK` with `{ "valid": false }`

#### Scenario: Malformed token string
- **WHEN** `POST /auth/validate` is called with a string that is not a valid JWT structure (e.g., missing segments)
- **THEN** the service returns `200 OK` with `{ "valid": false }`

#### Scenario: Missing token field
- **WHEN** `POST /auth/validate` is called with an empty body or a body missing the `token` field
- **THEN** the service returns `400 Bad Request` with `{ "error": "VALIDATION_ERROR", "message": "token is required" }`

#### Scenario: Unauthenticated access allowed
- **WHEN** `POST /auth/validate` is called without any `Authorization` header
- **THEN** the service processes the request normally (no authentication required for this endpoint)
