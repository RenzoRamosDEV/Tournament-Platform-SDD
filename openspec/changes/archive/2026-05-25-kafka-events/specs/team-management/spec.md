## MODIFIED Requirements

### Requirement: Team creation publishes event
When a team is created, the system SHALL publish a `team.created` event to Kafka via `transaction.on_commit`. The payload MUST include: `team_id` (int), `name` (str), `created_at` (ISO 8601 UTC string).

#### Scenario: Event published after team save
- **WHEN** a team is created and the DB transaction commits
- **THEN** a `team.created` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a team creation fails and the DB transaction rolls back
- **THEN** no `team.created` event is produced
