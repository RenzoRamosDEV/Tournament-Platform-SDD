## ADDED Requirements

### Requirement: List teams
The system SHALL expose `GET /api/teams/` returning a paginated list of all teams.
The endpoint SHALL be publicly accessible without authentication.
Each team object SHALL include: `id`, `name`, `owner` (user id), `created_at`.

#### Scenario: Public access returns paginated teams
- **WHEN** an unauthenticated client sends `GET /api/teams/`
- **THEN** the response status is `200 OK` and the body contains `count`, `next`, `previous`, and `results`

#### Scenario: Response fields are correct
- **WHEN** a client sends `GET /api/teams/`
- **THEN** each object in `results` contains `id`, `name`, `owner`, `created_at`

### Requirement: Create team
The system SHALL expose `POST /api/teams/` allowing any authenticated user to create a team.
The request body SHALL require `name` (non-empty string, max 100 chars).
The system SHALL automatically set `owner` to the authenticated user making the request.
The response on success SHALL be `201 Created` with the created team object.
The system SHALL reject a duplicate `name` with `400 Bad Request`.

#### Scenario: Authenticated user creates a team
- **WHEN** an authenticated user sends `POST /api/teams/` with `{ "name": "Team Alpha" }`
- **THEN** the response status is `201 Created` and the body contains the new team with `owner` set to the requesting user's id

#### Scenario: Unauthenticated request is rejected
- **WHEN** an unauthenticated client sends `POST /api/teams/` with a valid body
- **THEN** the response status is `401 Unauthorized`

#### Scenario: Missing name returns validation error
- **WHEN** an authenticated user sends `POST /api/teams/` with `{}`
- **THEN** the response status is `400 Bad Request` and the body identifies `name` as required

#### Scenario: Duplicate name returns error
- **WHEN** an authenticated user sends `POST /api/teams/` with a name already taken
- **THEN** the response status is `400 Bad Request`
