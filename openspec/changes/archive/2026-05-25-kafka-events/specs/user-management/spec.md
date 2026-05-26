## MODIFIED Requirements

### Requirement: User registration publishes event
When a user completes registration, the system SHALL publish a `user.registered` event to Kafka via `transaction.on_commit`. The payload MUST include: `user_id` (int), `email` (str), `registered_at` (ISO 8601 UTC string).

#### Scenario: Event published after user save
- **WHEN** a user registers and the DB transaction commits
- **THEN** a `user.registered` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a user registration fails and the DB transaction rolls back
- **THEN** no `user.registered` event is produced
