## ADDED Requirements

### Requirement: Serializer file responsibility boundary
Each app that accepts write operations SHALL contain exactly two serializer modules:
- `input.py` — serializers that validate and deserialise incoming request data
- `output.py` — serializers that serialise outgoing response data

The `rankings` app SHALL contain only `output.py` (read-only endpoint; no `input.py`).
No app listed below SHALL contain a file named `serializers.py` after this change is applied.

Required classes per app:

| App | `input.py` | `output.py` |
|---|---|---|
| `users` | `UserCreateSerializer` | `UserResponseSerializer`, `UserListSerializer` |
| `teams` | `TeamCreateSerializer` | `TeamResponseSerializer`, `TeamListSerializer` |
| `tournaments` | `TournamentCreateSerializer` | `TournamentResponseSerializer`, `TournamentListSerializer` |
| `matches` | `MatchReportSerializer` | `MatchResponseSerializer`, `MatchListSerializer` |
| `rankings` | *(none)* | `RankingResponseSerializer` |

#### Scenario: Write endpoint uses input serializer
- **WHEN** a viewset processes a `POST` or `PUT` request
- **THEN** the serializer class used is imported from `input.py`

#### Scenario: List endpoint uses ListSerializer
- **WHEN** a viewset processes a `GET` list request
- **THEN** the serializer class used is imported from `output.py` and is the `List` variant

#### Scenario: Detail endpoint uses ResponseSerializer
- **WHEN** a viewset processes a `GET /{id}/` request
- **THEN** the serializer class used is imported from `output.py` and is the `Response` variant

### Requirement: ListSerializer field subset
`ListSerializer` variants (e.g., `TeamListSerializer`) SHALL expose only summary fields:
`id`, `name`, `status`. Nested relations SHALL NOT appear in list responses.

#### Scenario: List response contains no nested objects
- **WHEN** a client sends `GET /api/teams/`
- **THEN** each item in `results` contains `id`, `name`, and `status` only — no nested team or user objects

### Requirement: ResponseSerializer full detail
`ResponseSerializer` variants (e.g., `TeamResponseSerializer`) SHALL expose the full object
including all nested relations.

#### Scenario: Detail response includes nested relations
- **WHEN** a client sends `GET /api/teams/{id}/`
- **THEN** the response body includes nested relations (e.g., owner details) alongside all scalar fields

### Requirement: No serializers.py in affected apps
After this change, importing from `<app>.serializers` in any of the five affected apps SHALL
raise `ModuleNotFoundError`. All import sites SHALL reference `<app>.input` or `<app>.output`.

#### Scenario: Removed serializers module
- **WHEN** a developer attempts `from teams.serializers import TeamCreateSerializer`
- **THEN** Python raises `ModuleNotFoundError`
