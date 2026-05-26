## Context

Django currently handles ranking recalculation, notifications, and audit logging synchronously inside API request handlers. All three concerns share the same database transaction and request lifecycle, meaning a failure in any one of them can affect the others. Introducing Kafka decouples these concerns: the API commits its DB write and publishes an event; downstream services consume that event independently at their own pace.

The platform is a Django REST Framework application backed by PostgreSQL, running in Docker Compose. Consumers will run as separate Docker Compose services.

## Goals / Non-Goals

**Goals:**
- Django publishes domain events to Kafka after (and only after) successful DB commit
- Three consumer processes run independently with retry logic and dead-letter queues
- All consumers are idempotent under at-least-once delivery
- Kafka broker is available in Docker Compose for local development
- Broker coordinates (bootstrap servers) are injected via environment variables

**Non-Goals:**
- Schema registry or Avro — plain JSON payloads only
- Kafka ACLs, SASL, or TLS for this phase
- Exactly-once delivery semantics (at-least-once is sufficient with idempotent consumers)
- Event replay tooling or consumer lag dashboards

## Decisions

### D1: Post-commit publish via `transaction.on_commit`
**Decision**: Use Django's `transaction.on_commit(lambda: publish_event(...))` to guarantee the event is only sent after the DB transaction commits.

**Rationale**: Publishing inside an `atomic()` block risks orphaned events — Kafka receives the message but the DB rolls back. `on_commit` hooks are not called on rollback, making this the safest integration point without a full outbox pattern.

**Alternative considered**: Transactional outbox pattern (write event to a DB table inside the same transaction; a separate process polls and publishes). More reliable under crash scenarios but adds operational complexity that is out of scope here.

### D2: Silent failure for unavailable Kafka broker
**Decision**: Wrap `producer.produce()` and `producer.flush()` in a try/except; log at ERROR level and return normally on failure.

**Rationale**: Kafka unavailability must not degrade the user-facing API. The DB write has already committed; surfacing a 500 to the client would be misleading. Error logs provide visibility for operators.

**Alternative considered**: Circuit breaker with a fallback queue. Provides better reliability guarantees but introduces a new dependency; deferred to a future iteration.

### D3: Each consumer is its own Docker Compose service with its own consumer group
**Decision**: `ranking-consumer`, `notification-consumer`, and `log-consumer` each run as a separate Docker Compose service, each configured with a unique `group.id`.

**Rationale**: Independent consumer group IDs mean Kafka tracks each consumer's offset separately. One consumer restarting does not affect the offset position of the others. Running as separate services gives independent restart policies.

### D4: Retry with exponential backoff in-process, then DLQ
**Decision**: Retry in-process up to 3 times (1s, 2s, 4s delays). On exhaustion, produce the raw message bytes to `{topic}.dlq` and commit the original offset.

**Rationale**: In-process retry avoids re-enqueuing to Kafka for transient failures (e.g., a brief DB hiccup). The DLQ preserves the message for manual inspection without blocking the consumer. Three retries with exponential backoff is a widely accepted default.

### D5: Idempotency strategy per consumer
- `ranking-consumer`: Check if an `EloHistory` record for `(match_id, team_id)` already exists before writing. Skip if present.
- `notification-consumer`: Check a `NotificationLog` table for `(match_id, notification_type)`. Skip if already sent.
- `log-consumer`: Use `(topic, match_id/entity_id)` uniqueness constraint on `event_log` or check before insert.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| `on_commit` hook not called in tests that don't wrap in a real transaction | Use `TestCase` (which wraps each test in a transaction and does call `on_commit`) or mock `transaction.on_commit` in unit tests |
| Producer silently drops events when Kafka is down | ERROR log + future outbox pattern; acceptable for current scope |
| DLQ messages accumulate without alerting | Operators must monitor `.dlq` topics manually; alerting is out of scope |
| Consumer idempotency checks add a DB read per event | Acceptable overhead; can be optimised with an upsert/INSERT IGNORE strategy |

## Migration Plan

1. Add `confluent-kafka` to `requirements.txt`
2. Extend `docker-compose.yml` with Kafka (KRaft mode, no Zookeeper dependency) and topic auto-creation
3. Create and run the `event_log` table migration
4. Implement the `publish_event` utility and wire `on_commit` hooks into existing views/services
5. Implement the three consumer scripts
6. Add consumer services to `docker-compose.yml`
7. Add `KAFKA_BOOTSTRAP_SERVERS` to `.env.example`

**Rollback**: Remove the `on_commit` hooks from the four affected services. Consumer processes can be stopped independently. No DB rollback needed — `event_log` table can remain.
