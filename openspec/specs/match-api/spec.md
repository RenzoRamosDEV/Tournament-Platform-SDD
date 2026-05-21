## ADDED Requirements

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

### Requirement: Report match result
The system SHALL expose `POST /api/matches/{id}/report/` allowing authenticated users
to submit a match result.
The request body SHALL require: `winner_id` (int), `score_team_a` (int ≥ 0),
`score_team_b` (int ≥ 0).
`winner_id` MUST equal the `id` of either `team_a` or `team_b` of the match.
On a valid first submission the system SHALL set `winner_team`, `score_a`, `score_b`,
`status="finished"`, and `played_at` to the current timestamp, then return `201 Created`.
If the match already has `status="finished"` and the requesting user's `role` is not `admin`,
the system SHALL return `409 Conflict`.
If the match already has `status="finished"` and the requesting user's `role` is `admin`,
the system SHALL overwrite the result and return `200 OK` with the updated match object.
If the match `{id}` does not exist the system SHALL return `404 Not Found`.
Unauthenticated requests SHALL return `401 Unauthorized`.

#### Scenario: First submission by authenticated user
- **WHEN** an authenticated user sends `POST /api/matches/42/report/` with `{ "winner_id": 7, "score_team_a": 3, "score_team_b": 1 }` and match 42 has no result
- **THEN** the response status is `201 Created`, `match.status` is `"finished"`, `winner_team` is `7`, `score_a` is `3`, `score_b` is `1`, and `played_at` is set

#### Scenario: Duplicate submission by non-admin is rejected
- **WHEN** an authenticated non-admin user sends `POST /api/matches/42/report/` and match 42 already has `status="finished"`
- **THEN** the response status is `409 Conflict`

#### Scenario: Admin overwrites existing result
- **WHEN** an authenticated admin sends `POST /api/matches/42/report/` with new scores and match 42 already has `status="finished"`
- **THEN** the response status is `200 OK` and the match reflects the updated result

#### Scenario: Match not found
- **WHEN** any authenticated user sends `POST /api/matches/9999/report/` and match 9999 does not exist
- **THEN** the response status is `404 Not Found`

#### Scenario: winner_id not in match returns validation error
- **WHEN** an authenticated user sends `POST /api/matches/42/report/` with a `winner_id` that is neither `team_a` nor `team_b`
- **THEN** the response status is `400 Bad Request`

#### Scenario: Unauthenticated request is rejected
- **WHEN** an unauthenticated client sends `POST /api/matches/42/report/`
- **THEN** the response status is `401 Unauthorized`
