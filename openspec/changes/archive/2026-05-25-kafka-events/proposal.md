## Why

Django currently calls ranking, notification, and logging logic synchronously inside the request cycle, creating tight coupling and a single point of failure. Introducing Kafka as an event bus lets each concern evolve and scale independently without any service needing to know about the others.

## What Changes

- New `publish_event` producer utility in Django — fires after DB commit, fails silently if Kafka is down
- Four Kafka topics created: `match.finished`, `tournament.created`, `user.registered`, `team.created`
- Three independent consumer processes: `ranking-consumer`, `notification-consumer`, `log-consumer`
- `event_log` database table for audit persistence by `log-consumer`
- Dead-letter topics (`*.dlq`) for messages that exhaust retry attempts
- Docker Compose extended with a Kafka broker service for local development
- Existing match-reporting, tournament-creation, user-registration, and team-creation flows updated to publish events post-commit

## Capabilities

### New Capabilities
- `kafka-producer`: Django utility for publishing domain events to Kafka after transaction commit
- `kafka-consumers`: Three independent consumer processes (ranking, notification, log) with retry, DLQ, and idempotency guarantees
- `event-log`: Persistent audit table storing every consumed event with topic, payload, and timestamp

### Modified Capabilities
- `match-tracking`: match result reporting now publishes a `match.finished` event post-commit
- `tournament-management`: tournament creation now publishes a `tournament.created` event post-commit
- `user-management`: user registration now publishes a `user.registered` event post-commit
- `team-management`: team creation now publishes a `team.created` event post-commit

## Impact

- **Dependencies**: `confluent-kafka` added to Python requirements
- **Infrastructure**: Docker Compose gains a Kafka broker (and Zookeeper or KRaft) service
- **Database**: New `event_log` table migration required
- **Environment variables**: `KAFKA_BOOTSTRAP_SERVERS` and per-topic env vars must be configured
- **Processes**: Three new long-running consumer processes must be managed (Docker Compose services or separate entrypoints)
- **No breaking API changes**: all existing REST endpoints remain unchanged; event publishing is additive
