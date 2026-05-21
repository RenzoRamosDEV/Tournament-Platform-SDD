## ADDED Requirements

### Requirement: Global throttle classes and rates
The system SHALL configure `AnonRateThrottle` and `UserRateThrottle` as `DEFAULT_THROTTLE_CLASSES`
in `REST_FRAMEWORK` with the following rates:
- `anon`: 100 requests per hour
- `user`: 1000 requests per hour

#### Scenario: Anonymous user within limit
- **WHEN** an unauthenticated client sends their 100th request within the current hour
- **THEN** the response status is `200 OK` (limit is inclusive)

#### Scenario: Authenticated user within limit
- **WHEN** an authenticated user sends their 1000th request within the current hour
- **THEN** the response status is `200 OK` (limit is inclusive)

### Requirement: HTTP 429 with structured JSON body
When any client exceeds its rate limit the system SHALL return `HTTP 429 Too Many Requests`
with the `Retry-After` header set to the integer seconds until the quota resets AND a JSON
body matching exactly:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Has superado el límite de solicitudes. Intenta de nuevo más tarde.",
  "retry_after_seconds": <integer>
}
```

`retry_after_seconds` SHALL be the ceiling of the remaining wait time in seconds (i.e.,
`math.ceil(exc.wait)`). No other body shape is acceptable.

This behaviour SHALL be implemented via a project-level `custom_exception_handler` registered
as `EXCEPTION_HANDLER` in `REST_FRAMEWORK`. The handler SHALL delegate all non-`Throttled`
exceptions to DRF's default handler.

#### Scenario: Anonymous user exceeds limit
- **WHEN** an unauthenticated client sends their 101st request within the current hour
- **THEN** the response status is `429`, the `Retry-After` header is present, and the body matches the JSON schema above

#### Scenario: Authenticated user exceeds limit
- **WHEN** an authenticated user sends their 1001st request within the current hour
- **THEN** the response status is `429`, the `Retry-After` header is present, and the body matches the JSON schema above

#### Scenario: retry_after_seconds is an integer
- **WHEN** the throttle wait time is 127.4 seconds
- **THEN** `retry_after_seconds` in the response body is `128`

#### Scenario: Non-throttle exceptions use default handler
- **WHEN** a view raises a `404 Not Found` exception
- **THEN** the response body is the standard DRF `{"detail": "Not found."}` shape, not the throttle body
