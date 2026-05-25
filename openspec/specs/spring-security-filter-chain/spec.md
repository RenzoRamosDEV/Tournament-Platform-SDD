## ADDED Requirements

### Requirement: Public and protected route configuration
The Spring Security filter chain MUST be configured as a `SecurityFilterChain` bean with the following access rules:
- **Unauthenticated access permitted**: `POST /auth/login`, `POST /auth/register`, `POST /auth/refresh`
- **Authentication required**: All other endpoints, including `POST /auth/validate` and `POST /auth/logout`

CSRF protection MAY be disabled for stateless JWT-based authentication.

#### Scenario: Login endpoint accessible without credentials
- **WHEN** an unauthenticated client sends `POST /auth/login` with valid credentials
- **THEN** the request reaches the controller and returns `200 OK` with tokens; Spring Security does not block it

#### Scenario: Validate endpoint requires authentication
- **WHEN** an unauthenticated client sends `POST /auth/validate` without an `Authorization` header
- **THEN** Spring Security returns `401 Unauthorized` with a JSON error body (not an HTML page or redirect)

#### Scenario: Register endpoint accessible without credentials
- **WHEN** an unauthenticated client sends `POST /auth/register` with registration data
- **THEN** the request reaches the controller without authentication checks

### Requirement: Structured JSON error bodies for 401 and 403
When Spring Security blocks a request with `401 Unauthorized` or `403 Forbidden`, the response MUST have `Content-Type: application/json` and a structured JSON body matching the global error format: `{ "error": "<code>", "message": "<human-readable>", "timestamp": "<ISO-8601>" }`. HTML responses or Spring's default error pages MUST NOT be returned.

#### Scenario: Unauthenticated access to protected route returns JSON 401
- **WHEN** a client accesses a protected endpoint without credentials
- **THEN** the response is `HTTP 401` with `Content-Type: application/json` and body `{ "error": "unauthorized", "message": "...", "timestamp": "..." }`

#### Scenario: Insufficient permissions returns JSON 403
- **WHEN** an authenticated client accesses an endpoint requiring a higher role
- **THEN** the response is `HTTP 403` with `Content-Type: application/json` and a structured error body; no HTML is returned
