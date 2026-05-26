## MODIFIED Requirements

### Requirement: Match result reporting publishes event
When a match result is reported and saved, the system SHALL publish a `match.finished` event to Kafka via `transaction.on_commit`. The payload MUST include: `match_id` (int), `team_a_id` (int), `team_b_id` (int), `winner_id` (int or null for a draw), `reported_at` (ISO 8601 UTC string).

#### Scenario: Event published after match save
- **WHEN** a match result is reported and the DB transaction commits
- **THEN** a `match.finished` event is produced with the correct payload fields

#### Scenario: No event on transaction rollback
- **WHEN** a match save operation fails and the DB transaction rolls back
- **THEN** no `match.finished` event is produced
