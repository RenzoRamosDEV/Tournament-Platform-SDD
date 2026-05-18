## ADDED Requirements

### Requirement: Leaderboard ranking query with B-tree index
The system SHALL define a B-tree index named `idx_users_elo` on `users(elo)`. A ranking
query SHALL select `username` and `elo` from `users`, order by `elo DESC`, and return
exactly 50 rows via `LIMIT 50`. Execution of `EXPLAIN ANALYZE` on this query MUST show
"Index Scan" or "Index Only Scan" on `idx_users_elo`.

#### Scenario: Index used for top-50 ranking
- **WHEN** the ranking query is executed on a table with at least 50 users
- **THEN** `EXPLAIN ANALYZE` output contains "idx_users_elo" and the result set has exactly 50 rows ordered by `elo` descending

#### Scenario: Index creation is idempotent
- **WHEN** `CREATE INDEX IF NOT EXISTS idx_users_elo ON users(elo)` is run twice
- **THEN** no error is raised and exactly one index named `idx_users_elo` exists

### Requirement: Team win aggregation — all-time and per-tournament
The system SHALL provide a query that joins `teams` and `matches`, groups by `teams.id`
and `teams.name`, counts rows where `matches.winner_team_id = teams.id`, and orders by
win count descending, returning columns `team_name` and `win_count`. A secondary variant
SHALL add `WHERE matches.tournament_id = <tournament_id>` to scope results to one
tournament.

#### Scenario: All-time wins ordered correctly
- **WHEN** the all-time wins query is executed with teams having 10, 7, and 3 wins across multiple tournaments
- **THEN** rows are returned in descending order: 10, 7, 3 — with no tournament filter applied

#### Scenario: Per-tournament filter excludes other tournaments
- **WHEN** the per-tournament variant is executed with a specific `tournament_id`
- **THEN** only wins from matches with that `tournament_id` are counted

#### Scenario: Team with zero wins is excluded
- **WHEN** a team has never been `winner_team_id` in any match
- **THEN** that team does not appear in either query result

### Requirement: Match listing with dual team-name resolution
The system SHALL provide a query that selects from `matches` and joins `teams` twice —
once aliased as `team_a` on `matches.team_a_id = team_a.id`, and once aliased as `team_b`
on `matches.team_b_id = team_b.id`. The result MUST include columns `match_id`,
`team_a_name`, `team_b_name`, `winner_team_id`, and `played_at`.

#### Scenario: Both team names resolved in one row
- **WHEN** the dual-join query is executed for a match between teams "Dragons" (id=1) and "Phoenix" (id=2)
- **THEN** the row contains `team_a_name = 'Dragons'` and `team_b_name = 'Phoenix'`

#### Scenario: All matches are returned regardless of status
- **WHEN** the query is executed with both pending and finished matches in the table
- **THEN** all matches appear — pending and finished alike

### Requirement: Transactional match-result reporting with ELO recalculation
When a match result is recorded, the following operations SHALL execute inside a single
`BEGIN … COMMIT` block in `psql`:

1. `UPDATE matches SET winner_team_id = <winner_team_id> WHERE id = <match_id>`
2. For each of the two participating users, `UPDATE users SET elo = ROUND((elo + 32 *
   (<actual_result> - 1.0 / (1 + power(10, (<opponent_elo> - elo) / 400.0))))::NUMERIC)::INTEGER
   WHERE id = <user_id>`, where `actual_result` is 1 for the winner and 0 for the loser.

If any statement raises an error the transaction MUST `ROLLBACK`, leaving all rows
unchanged. The block MUST be executable verbatim in `psql` using `\set` variable
substitution.

#### Scenario: Successful transaction persists all updates
- **WHEN** the transaction block is executed without errors for a valid match (user A elo=1200, user B elo=1000, A wins)
- **THEN** `matches.winner_team_id` is set, user A's elo increases above 1200, user B's elo decreases below 1000, and both changes persist after `COMMIT`

#### Scenario: Failed transaction rolls back all changes
- **WHEN** any statement within the `BEGIN … COMMIT` block raises an error
- **THEN** `ROLLBACK` is executed and all rows remain unchanged from their pre-transaction values

#### Scenario: ELO values remain integers after update
- **WHEN** the ELO recalculation produces a fractional result
- **THEN** the stored `elo` value is rounded to the nearest integer

### Requirement: Per-team match history ordered chronologically
Given a team identifier, the system SHALL return all matches where `team_a_id =
<team_id> OR team_b_id = <team_id>`, ordered by `played_at ASC`. Each row MUST
include `match_id`, `played_at`, the opposing team's `name` aliased as `opponent`,
and a `result` column derived with a `CASE` expression: `'win'` when `winner_team_id =
<team_id>`, `'loss'` otherwise.

#### Scenario: History ordered by date ascending
- **WHEN** the history query is executed for a team with matches on 2025-01-01, 2025-03-01, and 2025-02-01
- **THEN** rows are returned in the order 2025-01-01, 2025-02-01, 2025-03-01

#### Scenario: Result column computed correctly
- **WHEN** the team won a match and lost another
- **THEN** the `result` column reads `'win'` and `'loss'` respectively

#### Scenario: Opponent name resolved regardless of team slot
- **WHEN** the team appears as `team_a_id` in one match and `team_b_id` in another
- **THEN** the `opponent` column shows the correct opposing team name in both rows
