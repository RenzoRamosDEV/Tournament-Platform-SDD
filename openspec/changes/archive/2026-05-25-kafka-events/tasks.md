## 1. Infrastructure & Dependencies

- [x] 1.1 Add `confluent-kafka` to `requirements.txt`
- [x] 1.2 Extend `docker-compose.yml` with a Kafka broker service (KRaft mode) and pre-create the four topics plus their `.dlq` counterparts
- [x] 1.3 Add `KAFKA_BOOTSTRAP_SERVERS` to `.env.example` with a sensible local default

## 2. Kafka Producer Utility

- [x] 2.1 Write failing tests for `publish_event`: successful produce, silent failure when broker is unreachable, and assertion that it reads bootstrap servers from env
- [x] 2.2 Implement `publish_event(topic: str, payload: dict)` in `events/producer.py` — UTF-8 JSON, try/except with ERROR log, reads `KAFKA_BOOTSTRAP_SERVERS` from env
- [x] 2.3 Verify mutation score ≥ 95% for the producer module

## 3. event_log Model & Migration

- [x] 3.1 Write failing tests for the `EventLog` model (field types, `received_at` default)
- [x] 3.2 Create `EventLog` Django model with `topic`, `payload` (JSONField), `received_at` (auto-now-add)
- [x] 3.3 Generate and apply the migration

## 4. Domain Event Hooks (Producers)

- [x] 4.1 Write failing tests: `match.finished` event is published via `on_commit` after a match save, and NOT published on rollback
- [x] 4.2 Wire `transaction.on_commit(lambda: publish_event("match.finished", ...))` into match result reporting service/view
- [x] 4.3 Write failing tests for `tournament.created` on_commit hook
- [x] 4.4 Wire `tournament.created` event into tournament creation service/view
- [x] 4.5 Write failing tests for `user.registered` on_commit hook
- [x] 4.6 Wire `user.registered` event into user registration service/view
- [x] 4.7 Write failing tests for `team.created` on_commit hook
- [x] 4.8 Wire `team.created` event into team creation service/view

## 5. Consumer Base Infrastructure

- [x] 5.1 Write failing tests for the retry-with-backoff helper (3 retries, 1s/2s/4s delays, DLQ publish on exhaustion)
- [x] 5.2 Implement `events/consumer_base.py` with retry logic, exponential backoff, and DLQ produce on exhaustion
- [x] 5.3 Write failing tests for consumer group ID isolation (each consumer uses its own group.id)

## 6. ranking-consumer

- [x] 6.1 Write failing tests: ELO recalculation triggered for both teams; duplicate event is a no-op (idempotency via EloHistory check)
- [x] 6.2 Implement `consumers/ranking_consumer.py` subscribing to `match.finished`, triggering ELO recalculation, skipping if already processed
- [x] 6.3 Add `ranking-consumer` as a Docker Compose service with `group.id = ranking-service`

## 7. notification-consumer

- [x] 7.1 Write failing tests: notification dispatched to both teams; duplicate event is a no-op (idempotency via NotificationLog check)
- [x] 7.2 Implement `consumers/notification_consumer.py` subscribing to `match.finished`, dispatching notifications, skipping if already sent
- [x] 7.3 Add `notification-consumer` as a Docker Compose service with `group.id = notification-service`

## 8. log-consumer

- [x] 8.1 Write failing tests: one `event_log` row inserted per event across all four topics; duplicate event is a no-op
- [x] 8.2 Implement `consumers/log_consumer.py` subscribing to all four topics, inserting into `event_log`
- [x] 8.3 Add `log-consumer` as a Docker Compose service with `group.id = audit-log-service`

## 9. Integration & Mutation Testing

- [x] 9.1 Write an integration test (using a real or fake Kafka broker) covering the full publish → consume → persist flow for `match.finished`
- [x] 9.2 Run mutation testing across all new modules; ensure score ≥ 95% or document surviving mutants
