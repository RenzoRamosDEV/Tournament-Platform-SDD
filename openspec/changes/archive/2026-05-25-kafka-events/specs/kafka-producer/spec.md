## ADDED Requirements

### Requirement: Publish event after commit
The system SHALL provide a `publish_event(topic: str, payload: dict)` function that serializes `payload` as UTF-8 JSON and produces the message to the specified Kafka topic. This function MUST only be called inside a `transaction.on_commit` callback — never directly inside an `atomic()` block.

#### Scenario: Successful publish
- **WHEN** `publish_event("match.finished", {...})` is called after a committed DB transaction
- **THEN** the message is produced to the `match.finished` topic with UTF-8 encoded JSON value

#### Scenario: Function called via on_commit
- **WHEN** a DB transaction commits
- **THEN** `transaction.on_commit` fires `publish_event` with the correct topic and payload

### Requirement: Silent failure on broker unavailability
The system SHALL catch any exception raised by `producer.produce()` or `producer.flush()`, log the error at ERROR level including the topic name and the serialized payload, and return without raising.

#### Scenario: Kafka broker unreachable
- **WHEN** the Kafka broker is unavailable and `publish_event` is called
- **THEN** the exception is caught, an ERROR log entry is written with topic and payload, and no exception propagates to the caller

### Requirement: Configuration via environment variables
The producer SHALL read `KAFKA_BOOTSTRAP_SERVERS` from the environment. The value MUST NOT be hardcoded.

#### Scenario: Bootstrap servers from env
- **WHEN** the Django application starts
- **THEN** the Kafka producer is configured with the value of `KAFKA_BOOTSTRAP_SERVERS`
