## ADDED Requirements

### Requirement: Independent consumer processes
Each consumer (`ranking-consumer`, `notification-consumer`, `log-consumer`) SHALL run as a separate OS process with a unique `group.id` so Kafka tracks its offset independently.

#### Scenario: Consumers have distinct group IDs
- **WHEN** all three consumers are running
- **THEN** each is registered with Kafka under a different `group.id`: `ranking-service`, `notification-service`, `audit-log-service`

### Requirement: Retry with exponential backoff
On processing failure, a consumer SHALL retry the failed message up to 3 times with exponential backoff: 1s, 2s, 4s. Retries MUST be attempted before committing the offset.

#### Scenario: Transient failure recovers on retry
- **WHEN** a consumer fails on the first attempt and succeeds on the second
- **THEN** the message is processed successfully and the offset is committed; no DLQ entry is created

### Requirement: Dead-letter queue on retry exhaustion
After 3 failed retries, the consumer SHALL publish the raw message to `{original-topic}.dlq` and commit the offset on the original topic.

#### Scenario: All retries exhausted
- **WHEN** a consumer fails all 3 retry attempts for a `match.finished` message
- **THEN** the message is produced to `match.finished.dlq`, the offset on `match.finished` is committed, and the consumer moves on to the next message

### Requirement: Idempotent processing
All consumers SHALL be idempotent: processing the same message twice MUST NOT produce duplicate side effects.

#### Scenario: Duplicate event delivery to ranking-consumer
- **WHEN** `ranking-consumer` receives an already-processed `match.finished` event
- **THEN** ELO values are unchanged and no duplicate `EloHistory` record is created

#### Scenario: Duplicate event delivery to notification-consumer
- **WHEN** `notification-consumer` receives an already-processed `match.finished` event
- **THEN** no duplicate notification is dispatched

#### Scenario: Duplicate event delivery to log-consumer
- **WHEN** `log-consumer` receives an already-processed event
- **THEN** no duplicate row is inserted into `event_log`

### Requirement: ranking-consumer subscribes to match.finished
The `ranking-consumer` SHALL subscribe to the `match.finished` topic and trigger ELO recalculation for both `team_a_id` and `team_b_id` in the event payload.

#### Scenario: ELO recalculation triggered
- **WHEN** a `match.finished` event is consumed
- **THEN** ELO recalculation runs for both teams identified in the payload

### Requirement: notification-consumer subscribes to match.finished
The `notification-consumer` SHALL subscribe to `match.finished` and dispatch a notification to both teams.

#### Scenario: Notifications dispatched
- **WHEN** a `match.finished` event is consumed
- **THEN** a notification is sent to `team_a_id` and `team_b_id`

### Requirement: log-consumer subscribes to all topics
The `log-consumer` SHALL subscribe to `match.finished`, `tournament.created`, `user.registered`, and `team.created`, persisting each event to the `event_log` table.

#### Scenario: All topics consumed and logged
- **WHEN** one event is produced on each of the four topics
- **THEN** exactly four rows are inserted into `event_log` with the correct `topic` value
