## ADDED Requirements

### Requirement: Bearer token extraction and Java validation
The middleware SHALL extract the Bearer token from the `Authorization` header (case-insensitive scheme matching). It MUST call `POST {AUTH_SERVICE_URL}/auth/validate` with body `{ "token": "<token>" }` and a 2-second timeout. If the header is absent, `request.user` MUST be set to `AnonymousUser()` and the request passed through.

#### Scenario: Valid token sets request.user
- **WHEN** `Authorization: Bearer <valid_jwt>` is present and Java returns `{ "valid": true, "email": "u@x.com", "role": "player" }`
- **THEN** `request.user` is the Django `User` instance with `email = "u@x.com"` and the request proceeds

#### Scenario: No Authorization header passes through
- **WHEN** the request has no `Authorization` header
- **THEN** `request.user` is `AnonymousUser()` and the view receives the request normally

#### Scenario: Bearer scheme is case-insensitive
- **WHEN** `Authorization: bearer <valid_jwt>` (lowercase) is present
- **THEN** the token is extracted and validated identically to `Bearer`

### Requirement: Invalid token returns 401
The middleware MUST return `401 Unauthorized` with `Content-Type: application/json` and body `{ "error": "INVALID_TOKEN", "message": "Token is invalid or expired." }` when the Java service responds `{ "valid": false }`.

#### Scenario: Invalid token rejected
- **WHEN** `Authorization: Bearer <bad_token>` is present and Java returns `{ "valid": false }`
- **THEN** the middleware returns `401` with `{ "error": "INVALID_TOKEN" }` and the view is never called

### Requirement: Valid token with no matching Django user returns 401
If Java validates the token but no `User` with that email exists in the Django database, the middleware MUST return `401 Unauthorized` with body `{ "error": "USER_NOT_FOUND", "message": "Authenticated user does not exist in this system." }`.

#### Scenario: Ghost user
- **WHEN** Java returns `{ "valid": true, "email": "ghost@x.com" }` and no User with that email exists
- **THEN** the middleware returns `401` with `{ "error": "USER_NOT_FOUND" }`

### Requirement: Java service failure returns 503
The middleware MUST return `503 Service Unavailable` with body `{ "error": "AUTH_SERVICE_UNAVAILABLE", "message": "Authentication service is currently unavailable." }` if the Java call raises `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`, or receives an HTTP 5xx response.

#### Scenario: Java service timeout
- **WHEN** the Java call raises `requests.exceptions.Timeout`
- **THEN** the middleware returns `503` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`

#### Scenario: Java service returns 500
- **WHEN** the Java service responds with HTTP 500
- **THEN** the middleware returns `503` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`
