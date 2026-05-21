## ADDED Requirements

### Requirement: Global django-filter backend
The system SHALL register `DjangoFilterBackend` as the sole entry in `DEFAULT_FILTER_BACKENDS`
within `REST_FRAMEWORK`. Each viewset that supports filtering SHALL declare a `filterset_class`
pointing to a custom `FilterSet` subclass.

#### Scenario: Filter backend is active on filtered endpoint
- **WHEN** a client sends `GET /api/tournaments/?status=open`
- **THEN** the response contains only tournaments with `status="open"`

### Requirement: Strict status filter validation
For every endpoint that exposes a `?status=` filter, the system SHALL reject values outside
the allowed set with `HTTP 400 Bad Request`. The response body SHALL identify the field name
and list the accepted values. The system SHALL NOT return `HTTP 200` with an empty list for
an invalid status value.

Allowed values per endpoint:
- `GET /api/tournaments/` → `draft`, `open`, `in_progress`, `closed`
- `GET /api/matches/` → `scheduled`, `ongoing`, `finished`

#### Scenario: Invalid tournament status returns 400
- **WHEN** a client sends `GET /api/tournaments/?status=cancelled`
- **THEN** the response status is `400 Bad Request` and the body names the `status` field and lists `draft`, `open`, `in_progress`, `closed`

#### Scenario: Invalid match status returns 400
- **WHEN** a client sends `GET /api/matches/?status=postponed`
- **THEN** the response status is `400 Bad Request` and the body names the `status` field and lists `scheduled`, `ongoing`, `finished`

#### Scenario: Valid status returns 200
- **WHEN** a client sends `GET /api/matches/?status=ongoing`
- **THEN** the response status is `200 OK` and all objects in `results` have `status="ongoing"`

### Requirement: Per-endpoint filter field matrix
The system SHALL expose filter fields only as specified below. Endpoints not listed SHALL NOT
expose any filter parameters.

| Endpoint | Field | Type | Validation |
|---|---|---|---|
| `GET /api/tournaments/` | `status` | choice | `draft`, `open`, `in_progress`, `closed` → 400 on invalid |
| `GET /api/matches/` | `tournament_id` | integer FK | non-existent ID → 200 empty list |
| `GET /api/matches/` | `status` | choice | `scheduled`, `ongoing`, `finished` → 400 on invalid |
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
