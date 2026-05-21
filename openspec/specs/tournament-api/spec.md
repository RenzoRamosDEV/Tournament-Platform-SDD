## ADDED Requirements

### Requirement: List tournaments
The system SHALL expose `GET /api/tournaments/` returning a paginated list of tournaments.
The endpoint SHALL be publicly accessible without authentication.
Tournaments with `status="draft"` SHALL be excluded from results for unauthenticated users
and for authenticated users whose `role` is `player`.
Tournaments with `status="draft"` SHALL be included in results only for users with
`role` of `admin` or `organizer`.
The endpoint SHALL accept an optional `?status=` query parameter to filter results.
Valid values for `?status=` are: `draft`, `open`, `ongoing`, `finished`.
An invalid `?status=` value SHALL return `400 Bad Request`.
Each tournament object SHALL include: `id`, `name`, `status`, `format`, `max_teams`,
`start_date`, `end_date`, `created_by`.

#### Scenario: Public access excludes draft tournaments
- **WHEN** an unauthenticated client sends `GET /api/tournaments/`
- **THEN** the response status is `200 OK` and no tournament with `status="draft"` appears in `results`

#### Scenario: Admin sees draft tournaments
- **WHEN** an authenticated admin sends `GET /api/tournaments/`
- **THEN** tournaments with `status="draft"` appear in `results`

#### Scenario: Filter by valid status
- **WHEN** a client sends `GET /api/tournaments/?status=open`
- **THEN** the response status is `200 OK` and all objects in `results` have `status="open"`

#### Scenario: Filter by invalid status
- **WHEN** a client sends `GET /api/tournaments/?status=invalid`
- **THEN** the response status is `400 Bad Request`

### Requirement: Create tournament
The system SHALL expose `POST /api/tournaments/` allowing only users with `role="admin"`
to create a tournament.
Non-admin authenticated users SHALL receive `403 Forbidden`.
Unauthenticated requests SHALL receive `401 Unauthorized`.
The request body SHALL require: `name` (string), `start_date` (ISO 8601 date),
`end_date` (ISO 8601 date, MUST be ≥ `start_date`), `max_teams` (positive integer),
`format` (one of `single_elimination`, `round_robin`).
The system SHALL automatically set `created_by` to the authenticated admin user.
The initial `status` SHALL be `draft`.
The response on success SHALL be `201 Created` with the created tournament object.

#### Scenario: Admin creates a tournament
- **WHEN** an authenticated admin sends `POST /api/tournaments/` with all required fields
- **THEN** the response status is `201 Created`, the body contains the tournament with `status="draft"` and `created_by` set to the admin's id

#### Scenario: Non-admin is rejected
- **WHEN** an authenticated player sends `POST /api/tournaments/` with valid fields
- **THEN** the response status is `403 Forbidden`

#### Scenario: Unauthenticated request is rejected
- **WHEN** an unauthenticated client sends `POST /api/tournaments/`
- **THEN** the response status is `401 Unauthorized`

#### Scenario: end_date before start_date is rejected
- **WHEN** an admin sends `POST /api/tournaments/` with `end_date` before `start_date`
- **THEN** the response status is `400 Bad Request` and the body identifies the date constraint violation
