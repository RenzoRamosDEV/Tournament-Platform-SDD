## MODIFIED Requirements

### Requirement: List users
The system SHALL expose `GET /api/users/` returning a paginated list of all active users.
The endpoint SHALL be publicly accessible without authentication for unauthenticated reads.
The endpoint SHALL accept an optional `?role=` query parameter, but only admin users MAY use it;
a non-admin authenticated user or unauthenticated client that supplies `?role=` SHALL receive
`403 Forbidden`.
Valid values for `?role=` are defined by the `User.role` field choices. An invalid `?role=`
value supplied by an admin SHALL return `400 Bad Request`.
The response SHALL conform to the standard pagination envelope:
`{ "count": int, "next": url|null, "previous": url|null, "results": [ ... ] }`.
Each user object SHALL include: `id`, `username`, `email`, `role`, `elo`, `avatar_url`, `created_at`.

#### Scenario: Public access returns paginated users
- **WHEN** an unauthenticated client sends `GET /api/users/`
- **THEN** the response status is `200 OK` and the body contains `count`, `next`, `previous`, and `results`

#### Scenario: Admin filters by valid role
- **WHEN** an authenticated admin sends `GET /api/users/?role=player`
- **THEN** the response status is `200 OK` and all objects in `results` have `role="player"`

#### Scenario: Non-admin cannot use role filter
- **WHEN** a non-admin authenticated user sends `GET /api/users/?role=player`
- **THEN** the response status is `403 Forbidden`

#### Scenario: Admin supplies invalid role returns 400
- **WHEN** an authenticated admin sends `GET /api/users/?role=superuser`
- **THEN** the response status is `400 Bad Request` and the body identifies `role` and lists the valid choices
