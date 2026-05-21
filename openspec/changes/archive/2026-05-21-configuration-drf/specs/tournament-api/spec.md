## MODIFIED Requirements

### Requirement: List tournaments
The system SHALL expose `GET /api/tournaments/` returning a paginated list of tournaments.
The endpoint SHALL be publicly accessible without authentication.
Tournaments with `status="draft"` SHALL be excluded from results for unauthenticated users
and for authenticated users whose `role` is `player`.
Tournaments with `status="draft"` SHALL be included in results only for users with
`role` of `admin` or `organizer`.
The endpoint SHALL accept an optional `?status=` query parameter to filter results.
Valid values for `?status=` are: `draft`, `open`, `in_progress`, `closed`.
An invalid `?status=` value SHALL return `400 Bad Request` with a body identifying the
field and listing the accepted values.
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

#### Scenario: Filter by in_progress status
- **WHEN** a client sends `GET /api/tournaments/?status=in_progress`
- **THEN** the response status is `200 OK` and all objects in `results` have `status="in_progress"`

#### Scenario: Filter by invalid status returns 400
- **WHEN** a client sends `GET /api/tournaments/?status=cancelled`
- **THEN** the response status is `400 Bad Request` and the body lists `draft`, `open`, `in_progress`, `closed` as valid values
