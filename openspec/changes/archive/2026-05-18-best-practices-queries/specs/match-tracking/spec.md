## MODIFIED Requirements

### Requirement: Match record with score and status
The system SHALL persist a `matches` row with `tournament_id` (FK → `tournaments.id` ON DELETE RESTRICT), `team_a_id` (FK → `teams.id` ON DELETE RESTRICT), `team_b_id` (FK → `teams.id` ON DELETE RESTRICT), `winner_team_id` (FK → `teams.id` ON DELETE SET NULL, NULLABLE), `score_a` (INTEGER, NOT NULL, DEFAULT 0), `score_b` (INTEGER, NOT NULL, DEFAULT 0), `status` (CHECK IN `pending`, `ongoing`, `finished`, DEFAULT `pending`), and `played_at` (TIMESTAMP, NULLABLE).

#### Scenario: Match created with defaults
- **WHEN** a `matches` row is inserted with no explicit `score_a`, `score_b`, or `status`
- **THEN** `score_a` is 0, `score_b` is 0, `status` is `pending`, and `played_at` is NULL

#### Scenario: Invalid match status rejected
- **WHEN** a `matches` row is inserted with `status` not in (`pending`, `ongoing`, `finished`)
- **THEN** the database raises a CHECK constraint violation

## ADDED Requirements

### Requirement: ELO recalculation formula on match result
When a match result is recorded, the system SHALL recalculate the ELO rating for both
participating users using the standard Elo formula with K=32:

```
expected = 1.0 / (1 + 10 ^ ((opponent_elo - player_elo) / 400.0))
new_elo   = ROUND(old_elo + 32 * (actual_result - expected))
```

where `actual_result` is 1 for the winner and 0 for the loser. The resulting value MUST
be stored as an integer (rounded, not truncated). Both users' ELO values MUST be updated
atomically within the same database transaction as the `winner_team_id` update.

#### Scenario: Winner ELO increases after victory
- **WHEN** user A (elo=1200) defeats user B (elo=1000) and the transaction commits
- **THEN** user A's stored `elo` is greater than 1200

#### Scenario: Loser ELO decreases after defeat
- **WHEN** user A (elo=1200) defeats user B (elo=1000) and the transaction commits
- **THEN** user B's stored `elo` is less than 1000

#### Scenario: ELO update is atomic with match result
- **WHEN** the ELO update for user B fails after the `winner_team_id` update has been applied
- **THEN** the entire transaction rolls back and `winner_team_id` remains unchanged
