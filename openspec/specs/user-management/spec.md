## ADDED Requirements

### Requirement: User account creation with ELO
The system SHALL persist a `users` row with `username` (VARCHAR 150, UNIQUE, NOT NULL), `password_hash` (VARCHAR 255, NOT NULL), `role` (CHECK IN `admin`, `player`), `elo` (INTEGER, NOT NULL, DEFAULT 1000), and `created_at` (TIMESTAMP, NOT NULL, DEFAULT now()).

#### Scenario: New player registered with defaults
- **WHEN** a `users` row is inserted with `role = 'player'` and no explicit `elo`
- **THEN** `elo` is 1000 and `created_at` is the current timestamp

#### Scenario: Duplicate username rejected
- **WHEN** a `users` row is inserted with a `username` that already exists
- **THEN** the database raises a UNIQUE constraint violation

#### Scenario: Invalid role rejected
- **WHEN** a `users` row is inserted with `role` not in (`admin`, `player`)
- **THEN** the database raises a CHECK constraint violation

### Requirement: ELO descending index
The system SHALL maintain a descending index on `users.elo` to support efficient ranking queries.

#### Scenario: Ranking query uses index
- **WHEN** a query selects users ordered by `elo DESC`
- **THEN** the query plan uses the `elo` DESC index

### Requirement: Deletion guard on users
The system SHALL block deletion of a `users` row that is referenced by `teams.owner_id` or `team_members.user_id`.

#### Scenario: Owner deletion blocked
- **WHEN** a DELETE is issued on a `users` row that owns a team
- **THEN** the operation is rejected with a RESTRICT foreign key violation

#### Scenario: Member deletion blocked
- **WHEN** a DELETE is issued on a `users` row that is a member of a team
- **THEN** the operation is rejected with a RESTRICT foreign key violation

## MODIFIED Requirements

### Requirement: User registration publishes event
When a user completes registration, the system SHALL publish a `user.registered` event to Kafka via `transaction.on_commit`. The payload MUST include: `user_id` (int), `email` (str), `registered_at` (ISO 8601 UTC string).

#### Scenario: Event published after user save
- **WHEN** a user registers and the DB transaction commits
- **THEN** a `user.registered` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a user registration fails and the DB transaction rolls back
- **THEN** no `user.registered` event is produced
