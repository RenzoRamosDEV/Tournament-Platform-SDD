## ADDED Requirements

### Requirement: Global PageNumberPagination
The system SHALL configure `PageNumberPagination` as `DEFAULT_PAGINATION_CLASS` in the
global `REST_FRAMEWORK` dict with `PAGE_SIZE = 20`. All list endpoints SHALL return the
standard envelope: `{ "count": int, "next": url|null, "previous": url|null, "results": [...] }`.

#### Scenario: Default page size is 20
- **WHEN** a client sends any list request without a `?page=` parameter
- **THEN** the response contains at most 20 objects in `results`

#### Scenario: Explicit page navigation
- **WHEN** a client sends `GET /api/tournaments/?page=2`
- **THEN** the response contains `previous` pointing to page 1 and `results` with the next batch of tournaments

### Requirement: CursorPagination on matches endpoint
The `GET /api/matches/` endpoint SHALL use `CursorPagination` (set on `MatchViewSet.pagination_class`)
with `page_size = 20` and `ordering = "-played_at"`. The response envelope SHALL include
`next` and `previous` cursor URLs instead of page numbers. No other endpoint SHALL
declare a local `pagination_class`.

#### Scenario: Cursor pagination prevents duplicate records under concurrent writes
- **WHEN** new match records are inserted between two page requests on `GET /api/matches/`
- **THEN** the second cursor page returns the next set of matches without skipping or duplicating any row

#### Scenario: Cursor response omits count
- **WHEN** a client sends `GET /api/matches/`
- **THEN** the response body does NOT contain a `count` key (cursor pagination does not support total counts)
