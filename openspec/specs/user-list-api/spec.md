## ADDED Requirements

### Requirement: List users
The system SHALL expose `GET /api/users/` returning a paginated list of all active users.
The endpoint SHALL be publicly accessible without authentication.
The response SHALL conform to the standard pagination envelope:
`{ "count": int, "next": url|null, "previous": url|null, "results": [ ... ] }`.
Each user object SHALL include: `id`, `username`, `email`, `role`, `elo`, `avatar_url`, `created_at`.

#### Scenario: Public access returns paginated users
- **WHEN** an unauthenticated client sends `GET /api/users/`
- **THEN** the response status is `200 OK` and the body contains `count`, `next`, `previous`, and `results`

#### Scenario: Pagination parameters are respected
- **WHEN** a client sends `GET /api/users/?page=2&page_size=5`
- **THEN** the response contains at most 5 user objects and `previous` is non-null

#### Scenario: Response fields are correct
- **WHEN** a client sends `GET /api/users/`
- **THEN** each object in `results` contains `id`, `username`, `email`, `role`, `elo`, `avatar_url`, `created_at`
