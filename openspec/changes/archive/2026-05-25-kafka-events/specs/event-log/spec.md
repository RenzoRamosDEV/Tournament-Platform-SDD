## ADDED Requirements

### Requirement: event_log table
The system SHALL have an `event_log` database table with columns: `id` (auto-increment PK), `topic` (varchar, not null), `payload` (JSONB, not null), `received_at` (timestamp with timezone, not null, default now()).

#### Scenario: Table created by migration
- **WHEN** Django migrations are applied
- **THEN** the `event_log` table exists with all four required columns

### Requirement: log-consumer persists events
For every message consumed across all four topics, `log-consumer` SHALL insert one row into `event_log` with the `topic`, the full deserialized `payload`, and the current UTC timestamp as `received_at`.

#### Scenario: Event persisted on consumption
- **WHEN** `log-consumer` successfully processes a `match.finished` event
- **THEN** one row is inserted into `event_log` with `topic = 'match.finished'`, the correct payload, and a non-null `received_at`
