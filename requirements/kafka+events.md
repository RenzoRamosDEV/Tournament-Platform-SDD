# Requirements: Asynchronous Event Bus with Kafka

## Purpose
Decouple services by introducing Kafka as an event bus. Django acts as the sole producer; independent consumers react to domain events without Django knowing who is listening. This eliminates synchronous coupling between match reporting, ranking, notifications, and audit logging.

## Scope
- **In scope:**
  - Four system topics: `match.finished`, `tournament.created`, `user.registered`, `team.created`
  - Django producer using `confluent-kafka`; events published only after DB transaction commit
  - Three independent consumers: `ranking-consumer`, `notification-consumer`, `log-consumer`
  - At-least-once delivery with consumer-side idempotency
  - Dead-letter topic per consumer for unrecoverable failures
  - Kafka running via Docker Compose for local development
- **Out of scope:**
  - Schema registry or Avro serialization — plain JSON only
  - Kafka UI or monitoring dashboards (e.g., Kafdrop, Conduktor)
  - Per-consumer ACLs, SASL, or any Kafka authentication/authorization
  - Event replay or reprocessing tooling

## Requirements

1. A `publish_event(topic: str, payload: dict)` function MUST be called exclusively after the enclosing database transaction has been committed. It MUST NOT be called inside an open `atomic()` block.
2. If Kafka is unavailable at publish time, the failure MUST be caught, logged at ERROR level with the topic and payload, and the calling operation MUST NOT be rolled back or interrupted.
3. Each consumer MUST run in its own OS process with a unique consumer group ID so Kafka tracks its offset independently.
4. On processing failure, a consumer MUST retry up to **3 times** with **exponential backoff starting at 1 second** (i.e., 1s, 2s, 4s). After exhausting retries, the raw message MUST be published to a dead-letter topic named `{original-topic}.dlq` and the offset committed.
5. All consumers MUST be idempotent: receiving the same event twice MUST NOT produce duplicate side effects (e.g., duplicate ELO updates, duplicate notifications, duplicate log rows).
6. The `log-consumer` MUST subscribe to all four topics and persist each event to an `event_log` table with columns: `id`, `topic`, `payload` (JSONB), `received_at` (timestamp with timezone).
7. The `ranking-consumer` MUST subscribe to `match.finished` and trigger ELO recalculation for both teams in the event payload.
8. The `notification-consumer` MUST subscribe to `match.finished` and dispatch a notification to both teams identified in the event payload.
9. Event payloads MUST be serialized as UTF-8 encoded JSON. No other serialization format is permitted.
10. Kafka broker configuration (bootstrap servers, topics) MUST be read from environment variables, not hardcoded.

## Topics and Payload Contracts

| Topic               | Trigger                              | Required Payload Fields                                      |
|---------------------|--------------------------------------|--------------------------------------------------------------|
| `match.finished`    | Match result is reported             | `match_id` (int), `team_a_id` (int), `team_b_id` (int), `winner_id` (int or null for draw), `reported_at` (ISO 8601) |
| `tournament.created`| New tournament is created            | `tournament_id` (int), `name` (str), `created_at` (ISO 8601) |
| `user.registered`   | User completes registration          | `user_id` (int), `email` (str), `registered_at` (ISO 8601)   |
| `team.created`      | Team is created                      | `team_id` (int), `name` (str), `created_at` (ISO 8601)       |

## Consumer Groups

| Consumer                | Consumer Group ID            | Topics Subscribed        |
|-------------------------|------------------------------|--------------------------|
| `ranking-consumer`      | `ranking-service`            | `match.finished`         |
| `notification-consumer` | `notification-service`       | `match.finished`         |
| `log-consumer`          | `audit-log-service`          | all four topics          |

## Scenarios

### Successful Match Event Published and Consumed
- GIVEN a match result is saved and the DB transaction commits successfully
- WHEN `publish_event("match.finished", payload)` is called post-commit
- THEN the message appears on the `match.finished` topic within 1 second, `ranking-consumer` triggers ELO recalculation, `notification-consumer` dispatches a notification, and `log-consumer` inserts one row into `event_log`

### Kafka Unavailable at Publish Time
- GIVEN the Kafka broker is not reachable
- WHEN Django calls `publish_event` after a successful DB save
- THEN the exception is caught, an ERROR log entry is written containing the topic name and serialized payload, and the HTTP response to the caller is unaffected (no 500 error)

### Consumer Processing Failure with Retry Exhaustion
- GIVEN `ranking-consumer` receives a `match.finished` event and the ELO service raises an exception on every attempt
- WHEN the consumer retries 3 times (at 1s, 2s, 4s intervals) and all fail
- THEN the raw message is published to `match.finished.dlq`, the offset on `match.finished` is committed, and the consumer continues processing the next message

### Duplicate Event Delivery to ranking-consumer
- GIVEN a `match.finished` event is delivered twice due to a consumer restart before offset commit
- WHEN `ranking-consumer` processes the second delivery
- THEN ELO values for both teams are identical to what they were after the first processing (no double update)

### log-consumer Receives Events from All Topics
- GIVEN one event is produced on each of the four topics
- WHEN `log-consumer` processes all four messages
- THEN the `event_log` table contains exactly four new rows, each with the correct `topic` value and a non-null `received_at` timestamp
