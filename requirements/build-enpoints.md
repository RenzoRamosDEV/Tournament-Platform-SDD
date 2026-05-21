# Requirements: REST API Endpoints — Tournament Platform

## Purpose
Expose a REST API that allows users to list and manage users, teams, tournaments, and matches.
Read access is public; write operations require JWT authentication. The API integrates with
the existing Django backend and the tournament/match domain already defined in the schema.

## Scope
- **In scope:**
  - GET /api/users/ — list users (public, paginated)
  - GET /api/teams/ — list teams (public, paginated)
  - POST /api/teams/ — create a team (authenticated)
  - GET /api/tournaments/ — list tournaments with optional `?status=` filter (public, paginated)
  - POST /api/tournaments/ — create a tournament (admin only)
  - GET /api/matches/ — list matches with optional `?tournament_id=` filter (public, paginated)
  - POST /api/matches/{id}/report/ — report a match result (authenticated; admin can overwrite)
  - Pagination via `?page=` and `?page_size=` on all list endpoints
  - Tournament status filter validated against enum: `draft`, `open`, `in_progress`, `closed`

- **Out of scope:**
  - User registration or login endpoints
  - Team membership management (adding/removing players from a team)
  - Tournament bracket generation or scheduling logic
  - DELETE or PATCH operations on any resource
  - Filtering on endpoints other than those explicitly listed above

## Requirements

1. All GET endpoints are publicly accessible — no JWT required.
2. All POST endpoints require a valid JWT in the `Authorization: Bearer <token>` header; requests without a valid token return `401 Unauthorized`.
3. POST /api/tournaments/ is restricted to admin role; non-admin authenticated users receive `403 Forbidden`.
4. All list endpoints return paginated responses using `page` and `page_size` query parameters. The response envelope contains: `count` (int), `next` (URL or null), `previous` (URL or null), `results` (array).
5. GET /api/tournaments/ accepts an optional `?status=` query parameter. Valid values: `draft`, `open`, `in_progress`, `closed`. An invalid value returns `400 Bad Request` with a descriptive error message.
6. The `draft` status is visible only to users with admin or organizer roles; anonymous and player users cannot see draft tournaments in any listing.
7. GET /api/matches/ accepts an optional `?tournament_id=` query parameter to filter matches by tournament. If the given `tournament_id` does not exist, the response is an empty `results` list (not a 404).
8. POST /api/teams/ requires field `name` (non-empty string). Any authenticated user may create a team. Returns `201 Created` with the created team object.
9. POST /api/tournaments/ requires fields: `name` (string), `start_date` (ISO 8601 date), `end_date` (ISO 8601 date, must be ≥ start_date), `max_teams` (positive integer), `format` (string, e.g. `round_robin` or `elimination`). Returns `201 Created` with the created tournament object.
10. POST /api/matches/{id}/report/ requires body: `{ "winner_id": <int>, "score_team_a": <int>, "score_team_b": <int> }`. All three fields are required.
11. A match result can be submitted only once by non-admin users; a second POST from a non-admin to a match that already has a result returns `409 Conflict`.
12. An admin may overwrite an existing match result via POST /api/matches/{id}/report/; the response is `200 OK` with the updated match object.
13. If the match `{id}` does not exist, the report endpoint returns `404 Not Found`.
14. Validation errors on any POST endpoint return `400 Bad Request` with a JSON body describing each invalid field.

## Scenarios

### List Tournaments — Public Access
- GIVEN an unauthenticated client
- WHEN GET /api/tournaments/ is called
- THEN the response is `200 OK` with a paginated list of tournaments whose status is `open`, `in_progress`, or `closed`

### List Tournaments — Filter by Valid Status
- GIVEN an unauthenticated client
- WHEN GET /api/tournaments/?status=open is called
- THEN the response is `200 OK` with only tournaments whose status is `open`

### List Tournaments — Invalid Status Filter
- GIVEN an unauthenticated client
- WHEN GET /api/tournaments/?status=upcoming is called
- THEN the response is `400 Bad Request` with a message identifying `status` as invalid

### Draft Tournaments Hidden from Public
- GIVEN an unauthenticated client
- WHEN GET /api/tournaments/ is called (no status filter)
- THEN tournaments with status `draft` are not included in `results`

### Create Tournament — Admin Success
- GIVEN an authenticated admin user with a valid JWT
- WHEN POST /api/tournaments/ is called with `{ "name": "Spring Cup", "start_date": "2026-06-01", "end_date": "2026-06-30", "max_teams": 16, "format": "elimination" }`
- THEN the response is `201 Created` with the new tournament object including its assigned `id`

### Create Tournament — Non-Admin Rejected
- GIVEN an authenticated player user with a valid JWT
- WHEN POST /api/tournaments/ is called with valid fields
- THEN the response is `403 Forbidden`

### Create Team — Authenticated User
- GIVEN an authenticated user with a valid JWT
- WHEN POST /api/teams/ is called with `{ "name": "Team Alpha" }`
- THEN the response is `201 Created` with the new team object

### Create Team — Unauthenticated
- GIVEN an unauthenticated client
- WHEN POST /api/teams/ is called
- THEN the response is `401 Unauthorized`

### Report Match Result — First Submission
- GIVEN an authenticated user with a valid JWT and a match with no existing result
- WHEN POST /api/matches/42/report/ is called with `{ "winner_id": 7, "score_team_a": 3, "score_team_b": 1 }`
- THEN the response is `201 Created` with the updated match object reflecting the result

### Report Match Result — Duplicate by Non-Admin
- GIVEN an authenticated non-admin user and match 42 already has a reported result
- WHEN POST /api/matches/42/report/ is called again
- THEN the response is `409 Conflict`

### Report Match Result — Admin Overwrite
- GIVEN an authenticated admin user and match 42 already has a reported result
- WHEN POST /api/matches/42/report/ is called with updated scores
- THEN the response is `200 OK` with the match object reflecting the new result

### Report Match Result — Match Not Found
- GIVEN any authenticated user
- WHEN POST /api/matches/9999/report/ is called and match 9999 does not exist
- THEN the response is `404 Not Found`

### Pagination — Default Behavior
- GIVEN an unauthenticated client
- WHEN GET /api/teams/ is called without pagination params
- THEN the response includes `count`, `next`, `previous`, and `results` fields using server-default page size
