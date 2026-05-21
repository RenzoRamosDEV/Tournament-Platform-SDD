## MODIFIED Requirements

### Requirement: List matches
The system SHALL expose `GET /api/matches/` returning a paginated list of matches.
The endpoint SHALL be publicly accessible without authentication.
The endpoint SHALL use `CursorPagination` with `page_size = 20` and `ordering = "-played_at"`.
The endpoint SHALL accept an optional `?tournament_id=` query parameter to filter matches
by tournament. If the given `tournament_id` references a non-existent tournament, the
response SHALL be `200 OK` with an empty `results` list.
The endpoint SHALL accept an optional `?status=` query parameter. Valid values are
`scheduled`, `ongoing`, `finished`. An invalid `?status=` value SHALL return `400 Bad Request`
with a body identifying the field and listing accepted values.
Each match object in list responses SHALL include: `id`, `tournament`, `team_a`, `team_b`, `status`.

#### Scenario: Public access returns cursor-paginated matches
- **WHEN** an unauthenticated client sends `GET /api/matches/`
- **THEN** the response status is `200 OK` and the body contains `next`, `previous`, and `results` (no `count` key)

#### Scenario: Filter by existing tournament
- **WHEN** a client sends `GET /api/matches/?tournament_id=1`
- **THEN** all objects in `results` have `tournament` equal to `1`

#### Scenario: Filter by non-existent tournament returns empty list
- **WHEN** a client sends `GET /api/matches/?tournament_id=9999` and tournament 9999 does not exist
- **THEN** the response status is `200 OK` and `results` is an empty array

#### Scenario: Filter by valid status
- **WHEN** a client sends `GET /api/matches/?status=ongoing`
- **THEN** the response status is `200 OK` and all objects in `results` have `status="ongoing"`

#### Scenario: Filter by invalid status returns 400
- **WHEN** a client sends `GET /api/matches/?status=postponed`
- **THEN** the response status is `400 Bad Request` and the body lists `scheduled`, `ongoing`, `finished` as valid values

#### Scenario: Cursor stays consistent under concurrent inserts
- **WHEN** new match records are inserted between two paginated requests
- **THEN** the cursor page returns the next batch without skipping or duplicating any match
