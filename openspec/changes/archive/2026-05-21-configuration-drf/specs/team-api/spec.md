## MODIFIED Requirements

### Requirement: List teams
The system SHALL expose `GET /api/teams/` returning a paginated list of all teams.
The endpoint SHALL be publicly accessible without authentication.
The endpoint SHALL accept an optional `?tournament_id=` query parameter to filter results
to teams registered in that tournament. If the given `tournament_id` references a
non-existent tournament, the response SHALL be `200 OK` with an empty `results` list.
Each team object in list responses SHALL include: `id`, `name`, `status`.

#### Scenario: Public access returns paginated teams
- **WHEN** an unauthenticated client sends `GET /api/teams/`
- **THEN** the response status is `200 OK` and the body contains `count`, `next`, `previous`, and `results`

#### Scenario: Filter by existing tournament
- **WHEN** a client sends `GET /api/teams/?tournament_id=2`
- **THEN** the response contains only teams registered in tournament 2

#### Scenario: Filter by non-existent tournament returns empty list
- **WHEN** a client sends `GET /api/teams/?tournament_id=9999` and tournament 9999 does not exist
- **THEN** the response status is `200 OK` and `results` is an empty array
