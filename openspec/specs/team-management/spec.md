## ADDED Requirements

### Requirement: Team creation with owner
The system SHALL persist a `teams` row with `name` (VARCHAR 100, UNIQUE, NOT NULL), `owner_id` (FK → `users.id` ON DELETE RESTRICT), and `created_at` (TIMESTAMP, NOT NULL, DEFAULT now()).

#### Scenario: Team created successfully
- **WHEN** a `teams` row is inserted with a valid `owner_id`
- **THEN** the team is persisted with `created_at` set to now

#### Scenario: Duplicate team name rejected
- **WHEN** a `teams` row is inserted with a `name` that already exists
- **THEN** the database raises a UNIQUE constraint violation

#### Scenario: Team owner not auto-added as member
- **WHEN** a `teams` row is inserted
- **THEN** no corresponding `team_members` row is created automatically

### Requirement: Team membership via junction table
The system SHALL persist team membership in `team_members` with a composite primary key (`user_id`, `team_id`), `joined_at` (TIMESTAMP, NOT NULL, DEFAULT now()), and FK ON DELETE RESTRICT on both columns.

#### Scenario: Member added to team
- **WHEN** a `team_members` row is inserted with a valid (`user_id`, `team_id`) pair
- **THEN** the row is persisted with `joined_at` set to now

#### Scenario: Duplicate membership rejected
- **WHEN** a `team_members` row is inserted with a (`user_id`, `team_id`) pair that already exists
- **THEN** the database raises a UNIQUE/PK constraint violation

#### Scenario: Member deletion blocked
- **WHEN** a DELETE is issued on a `teams` row that has members
- **THEN** the operation is rejected with a RESTRICT foreign key violation

## MODIFIED Requirements

### Requirement: Team creation publishes event
When a team is created, the system SHALL publish a `team.created` event to Kafka via `transaction.on_commit`. The payload MUST include: `team_id` (int), `name` (str), `created_at` (ISO 8601 UTC string).

#### Scenario: Event published after team save
- **WHEN** a team is created and the DB transaction commits
- **THEN** a `team.created` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a team creation fails and the DB transaction rolls back
- **THEN** no `team.created` event is produced
