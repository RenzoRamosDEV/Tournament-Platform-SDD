## ADDED Requirements

### Requirement: Tournament lifecycle with status and format constraints
The system SHALL persist a `tournaments` row with `name` (VARCHAR 200, NOT NULL), `status` (CHECK IN `draft`, `open`, `ongoing`, `finished`, DEFAULT `draft`), `format` (CHECK IN `single_elim`, `round_robin`), `max_teams` (INTEGER, CHECK > 0), `start_date` (DATE, NOT NULL), and `end_date` (DATE, NOT NULL, CHECK `end_date >= start_date`).

#### Scenario: Tournament created with default status
- **WHEN** a `tournaments` row is inserted with no explicit `status`
- **THEN** `status` is `draft`

#### Scenario: Invalid status rejected
- **WHEN** a `tournaments` row is inserted with `status` not in (`draft`, `open`, `ongoing`, `finished`)
- **THEN** the database raises a CHECK constraint violation

#### Scenario: Invalid format rejected
- **WHEN** a `tournaments` row is inserted with `format` not in (`single_elim`, `round_robin`)
- **THEN** the database raises a CHECK constraint violation

#### Scenario: end_date before start_date rejected
- **WHEN** a `tournaments` row is inserted with `end_date < start_date`
- **THEN** the database raises a CHECK constraint violation

#### Scenario: max_teams zero or negative rejected
- **WHEN** a `tournaments` row is inserted with `max_teams <= 0`
- **THEN** the database raises a CHECK constraint violation

### Requirement: Tournament team registration
The system SHALL persist team registrations in `tournament_teams` with a composite primary key (`tournament_id`, `team_id`), `registered_at` (TIMESTAMP, NOT NULL, DEFAULT now()), and FK ON DELETE RESTRICT on both columns.

#### Scenario: Team registered for tournament
- **WHEN** a `tournament_teams` row is inserted with a valid (`tournament_id`, `team_id`) pair
- **THEN** the row is persisted with `registered_at` set to now

#### Scenario: Duplicate registration rejected
- **WHEN** a `tournament_teams` row is inserted with a (`tournament_id`, `team_id`) pair that already exists
- **THEN** the database raises a UNIQUE/PK constraint violation
