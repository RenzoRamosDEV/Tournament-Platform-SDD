## ADDED Requirements

### Requirement: Uniform JSON error structure
A `@RestControllerAdvice` class SHALL translate all thrown exceptions into a uniform JSON response structure:
```json
{ "error": "<code>", "message": "<human-readable>", "timestamp": "<ISO-8601>" }
```
All error responses MUST have `Content-Type: application/json`. No exception type SHALL result in an HTML error page or an unstructured response body.

#### Scenario: AuthenticationException returns 401 JSON
- **WHEN** an `AuthenticationException` is thrown anywhere in the request processing chain
- **THEN** the response is `HTTP 401` with `Content-Type: application/json` and body `{ "error": "unauthorized", "message": "<reason>", "timestamp": "<ISO-8601>" }`

#### Scenario: JwtException returns 401 JSON
- **WHEN** a `JwtException` (e.g., expired or malformed JWT) is thrown
- **THEN** the response is `HTTP 401` with `{ "error": "invalid_token", "message": "<reason>", "timestamp": "<ISO-8601>" }`

### Requirement: Validation error response
`MethodArgumentNotValidException` and `ConstraintViolationException` MUST be translated to `HTTP 400 Bad Request` with a message that includes field-level detail.

#### Scenario: Missing required field returns 400 with field detail
- **WHEN** a client submits a registration request with a missing required field and `MethodArgumentNotValidException` is thrown
- **THEN** the response is `HTTP 400` with body `{ "error": "validation_error", "message": "<field>: <constraint violation detail>", "timestamp": "<ISO-8601>" }`

#### Scenario: ConstraintViolationException returns 400
- **WHEN** a `ConstraintViolationException` is thrown (e.g., from `@Validated` method parameter)
- **THEN** the response is `HTTP 400` with a structured error body

### Requirement: Not found and generic error responses
`EntityNotFoundException` MUST return `HTTP 404`. Any unhandled `Exception` MUST return `HTTP 500` with `{ "error": "internal_server_error", "message": "An unexpected error occurred.", "timestamp": "<ISO-8601>" }`. The 500 handler MUST NOT leak stack traces or implementation details in the response body.

#### Scenario: EntityNotFoundException returns 404
- **WHEN** `EntityNotFoundException` is thrown (e.g., user not found)
- **THEN** the response is `HTTP 404` with `{ "error": "not_found", "message": "<entity> not found.", "timestamp": "<ISO-8601>" }`

#### Scenario: Unhandled exception returns 500 without stack trace
- **WHEN** an unhandled `RuntimeException` propagates to the exception handler
- **THEN** the response is `HTTP 500` with `{ "error": "internal_server_error", "message": "An unexpected error occurred.", "timestamp": "<ISO-8601>" }` and NO stack trace in the body
