## ADDED Requirements

### Requirement: No unhandled exceptions propagate to Django error handler
The JWT middleware MUST catch all exceptions that can arise from the outbound HTTP call (including but not limited to `requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`, and any unexpected `Exception`). The middleware MUST NOT allow any exception to propagate to Django's default error handler. All error cases MUST produce a structured `JsonResponse` with the appropriate HTTP status code.

#### Scenario: Unexpected exception is caught and returns 503
- **WHEN** the outbound call to the auth service raises an unexpected exception (e.g., `ValueError`, `OSError`)
- **THEN** the middleware catches it and returns `HTTP 503` with `{ "error": "AUTH_SERVICE_UNAVAILABLE", "message": "Authentication service is currently unavailable." }`; Django's 500 handler is never invoked

#### Scenario: No unhandled exception escapes middleware
- **WHEN** any exception occurs during auth service communication
- **THEN** the middleware always returns a `JsonResponse` and the exception does not reach Django's exception middleware

## MODIFIED Requirements

### Requirement: Java service failure returns 503
The middleware MUST return `503 Service Unavailable` with body `{ "error": "AUTH_SERVICE_UNAVAILABLE", "message": "Authentication service is currently unavailable." }` if the Java call raises `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`, any other network-related exception, or receives an HTTP 5xx response. The outbound HTTP call MUST have a hard timeout of **2 seconds**. The middleware MUST NOT re-raise any exception.

#### Scenario: Java service timeout
- **WHEN** the Java call raises `requests.exceptions.Timeout`
- **THEN** the middleware returns `503` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`

#### Scenario: Java service returns 500
- **WHEN** the Java service responds with HTTP 500
- **THEN** the middleware returns `503` with `{ "error": "AUTH_SERVICE_UNAVAILABLE" }`

#### Scenario: Hard 2-second timeout enforced
- **WHEN** the outbound call to the auth service is made
- **THEN** the `requests` call includes `timeout=2`; calls exceeding 2 seconds raise `Timeout` and are handled as above
