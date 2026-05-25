## ADDED Requirements

### Requirement: Date range filtering on list endpoints
The `GET /api/tournaments/` and `GET /api/matches/` endpoints SHALL support date range filtering via `date_from` and `date_to` query parameters (ISO-8601 date format: `YYYY-MM-DD`). When provided, results MUST be filtered to objects whose relevant date field falls within the specified range (inclusive). Invalid date formats MUST return `HTTP 400 Bad Request`.

#### Scenario: Tournament date range filter
- **WHEN** a client sends `GET /api/tournaments/?date_from=2024-01-01&date_to=2024-06-30`
- **THEN** the response contains only tournaments whose start date falls between 2024-01-01 and 2024-06-30 (inclusive)

#### Scenario: Invalid date format returns 400
- **WHEN** a client sends `GET /api/tournaments/?date_from=not-a-date`
- **THEN** the response is `HTTP 400 Bad Request` with a structured error body identifying the invalid parameter

### Requirement: Owner/creator ID filtering
The `GET /api/tournaments/` endpoint SHALL support filtering by `created_by` (integer user ID) query parameter. Results MUST be limited to tournaments created by the specified user. A non-existent user ID MUST return `HTTP 200` with an empty result list.

#### Scenario: Filter tournaments by creator
- **WHEN** a client sends `GET /api/tournaments/?created_by=5`
- **THEN** the response contains only tournaments where `created_by_id = 5`

#### Scenario: Non-existent creator ID returns empty list
- **WHEN** a client sends `GET /api/tournaments/?created_by=99999` and user 99999 does not exist
- **THEN** the response is `HTTP 200` with `results: []`

## MODIFIED Requirements

### Requirement: Per-endpoint filter field matrix
The system SHALL expose filter fields only as specified below. Endpoints not listed SHALL NOT expose any filter parameters.

| Endpoint | Field | Type | Validation |
|---|---|---|---|
| `GET /api/tournaments/` | `status` | choice | `draft`, `open`, `in_progress`, `closed` → 400 on invalid |
| `GET /api/tournaments/` | `date_from` | date | ISO-8601 `YYYY-MM-DD` → 400 on invalid format |
| `GET /api/tournaments/` | `date_to` | date | ISO-8601 `YYYY-MM-DD` → 400 on invalid format |
| `GET /api/tournaments/` | `created_by` | integer FK | non-existent ID → 200 empty list |
| `GET /api/matches/` | `tournament_id` | integer FK | non-existent ID → 200 empty list |
| `GET /api/matches/` | `status` | choice | `scheduled`, `ongoing`, `finished` → 400 on invalid |
| `GET /api/matches/` | `date_from` | date | ISO-8601 `YYYY-MM-DD` → 400 on invalid format |
| `GET /api/matches/` | `date_to` | date | ISO-8601 `YYYY-MM-DD` → 400 on invalid format |
| `GET /api/teams/` | `tournament_id` | integer FK | non-existent ID → 200 empty list |
| `GET /api/users/` | `role` | choice | allowed values from `User.role` choices → 400 on invalid; endpoint is admin-only |
| `GET /api/rankings/` | `tournament_id` | integer FK | non-existent ID → 200 empty list |

#### Scenario: Filter by non-existent tournament_id returns empty list
- **WHEN** a client sends `GET /api/matches/?tournament_id=9999` and tournament 9999 does not exist
- **THEN** the response status is `200 OK` and `results` is an empty array

#### Scenario: Teams filtered by tournament
- **WHEN** a client sends `GET /api/teams/?tournament_id=3`
- **THEN** the response contains only teams registered in tournament 3

#### Scenario: Non-admin cannot access user role filter
- **WHEN** a non-admin authenticated user sends `GET /api/users/?role=player`
- **THEN** the response status is `403 Forbidden`
