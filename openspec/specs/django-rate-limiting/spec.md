## ADDED Requirements

### Requirement: Per-IP rate limits on critical endpoints
The system SHALL enforce rate limiting on at minimum the following endpoints:
- Login proxy (`POST /api/auth/login/`)
- Token refresh proxy (`POST /api/auth/refresh/`)
- Match result submission (`POST /api/matches/{id}/report/`)

Rate limits:
- Unauthenticated requests: **5 requests per minute** per IP address
- Authenticated requests: **60 requests per minute** per IP address

Requests exceeding the limit MUST receive `HTTP 429 Too Many Requests` with a `Retry-After` header indicating when the client may retry.

#### Scenario: Unauthenticated burst to login endpoint rejected
- **WHEN** an unauthenticated client sends 6 requests to `POST /api/auth/login/` within a 60-second window
- **THEN** the 6th request receives `HTTP 429` with a `Retry-After` header; the first 5 requests succeed normally

#### Scenario: Authenticated requests have higher limit
- **WHEN** an authenticated client sends 60 requests to `POST /api/matches/{id}/report/` within a minute
- **THEN** all 60 requests are processed; the 61st request receives `HTTP 429`

#### Scenario: Rate limit resets after window
- **WHEN** an unauthenticated client has triggered the 429 limit and the rate window expires
- **THEN** subsequent requests are accepted again up to the limit

### Requirement: 429 response includes Retry-After header
When a rate limit is exceeded, the response MUST include a `Retry-After` header with the number of seconds until the rate limit window resets. The response body SHOULD include a JSON body `{ "error": "rate_limit_exceeded", "message": "Too many requests. Please try again later." }`.

#### Scenario: Retry-After header present on 429
- **WHEN** a client receives `HTTP 429` from any rate-limited endpoint
- **THEN** the response headers include `Retry-After: <seconds>` where `<seconds>` is a positive integer

### Requirement: Rate limiting uses cache backend
The rate limiting implementation SHALL use Django's cache framework as its storage backend. In production, the cache backend MUST be shared across processes (e.g., Redis or Memcached). In tests, `LocMemCache` is acceptable.

#### Scenario: Rate limit is enforced across requests in same window
- **WHEN** the same IP sends requests across multiple Django worker processes
- **THEN** the rate limit counter is consistent (not per-process)
