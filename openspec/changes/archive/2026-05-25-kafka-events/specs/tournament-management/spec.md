## MODIFIED Requirements

### Requirement: Tournament creation publishes event
When a tournament is created, the system SHALL publish a `tournament.created` event to Kafka via `transaction.on_commit`. The payload MUST include: `tournament_id` (int), `name` (str), `created_at` (ISO 8601 UTC string).

#### Scenario: Event published after tournament save
- **WHEN** a tournament is created and the DB transaction commits
- **THEN** a `tournament.created` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a tournament creation fails and the DB transaction rolls back
- **THEN** no `tournament.created` event is produced
