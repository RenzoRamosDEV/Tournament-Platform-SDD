## MODIFIED Requirements

### Requirement: Global PageNumberPagination
The system SHALL configure `PageNumberPagination` as `DEFAULT_PAGINATION_CLASS` in the global `REST_FRAMEWORK` dict with `PAGE_SIZE = 20` and `MAX_PAGE_SIZE = 100`. All list endpoints SHALL return the standard envelope: `{ "count": int, "next": url|null, "previous": url|null, "results": [...] }`. Clients SHALL be able to override page size via the `page_size` query parameter, up to a maximum of 100 items. Requests with `page_size` exceeding 100 MUST be clamped to 100 or rejected with `HTTP 400`.

#### Scenario: Default page size is 20
- **WHEN** a client sends any list request without a `?page_size=` parameter
- **THEN** the response contains at most 20 objects in `results`

#### Scenario: Client overrides page size within limit
- **WHEN** a client sends `GET /api/tournaments/?page_size=50`
- **THEN** the response contains at most 50 objects in `results`

#### Scenario: Client requests page size above maximum
- **WHEN** a client sends `GET /api/tournaments/?page_size=200`
- **THEN** the response contains at most 100 objects in `results` (clamped to max)

#### Scenario: Explicit page navigation
- **WHEN** a client sends `GET /api/tournaments/?page=2`
- **THEN** the response contains `previous` pointing to page 1 and `results` with the next batch of tournaments
