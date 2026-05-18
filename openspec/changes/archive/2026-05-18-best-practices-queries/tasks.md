## 1. Index Setup

- [x] 1.1 Write failing test: assert `idx_users_elo` does not yet exist on `users(elo)`
- [x] 1.2 Create B-tree index: `CREATE INDEX IF NOT EXISTS idx_users_elo ON users(elo)`
- [x] 1.3 Verify with `EXPLAIN ANALYZE` that the ranking query uses `idx_users_elo`

## 2. Leaderboard Ranking Query

- [x] 2.1 Write failing test: seeded dataset returns top 50 users ordered by `elo DESC`
- [x] 2.2 Write ranking query: `SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50`
- [x] 2.3 Run `EXPLAIN ANALYZE` and confirm "Index Scan" or "Index Only Scan" on `idx_users_elo`

## 3. Team Win Aggregation Query

- [x] 3.1 Write failing test: all-time query returns correct `win_count` per team across multiple tournaments
- [x] 3.2 Write all-time wins query using `JOIN teams … GROUP BY teams.id, teams.name` with `COUNT CASE WHEN winner_team_id = teams.id`
- [x] 3.3 Write failing test: per-tournament variant excludes matches from other tournaments
- [x] 3.4 Add `WHERE matches.tournament_id = <tournament_id>` variant and verify it filters correctly

## 4. Dual Team-Name Match Listing Query

- [x] 4.1 Write failing test: query returns `team_a_name` and `team_b_name` resolved from two separate joins
- [x] 4.2 Write the query joining `teams AS team_a ON team_a_id = team_a.id` and `teams AS team_b ON team_b_id = team_b.id`
- [x] 4.3 Confirm result columns: `match_id`, `team_a_name`, `team_b_name`, `winner_team_id`, `played_at`

## 5. Transactional ELO Recalculation

- [x] 5.1 Write failing test: after transaction commits, winner's `elo` increases and loser's `elo` decreases
- [x] 5.2 Write the `BEGIN … COMMIT` block that updates `matches.winner_team_id` and both users' `elo` using K=32 formula with `ROUND(…::NUMERIC)::INTEGER`
- [x] 5.3 Write failing test: a forced error in the second UPDATE causes full rollback
- [x] 5.4 Verify rollback by simulating an error (e.g., update nonexistent `user_id`) and confirming no rows changed
- [x] 5.5 Document `\set` variable substitution convention so block is runnable verbatim in `psql`

## 6. Per-Team Match History Query

- [x] 6.1 Write failing test: history returns all matches for a team sorted by `played_at ASC`
- [x] 6.2 Write query with `WHERE team_a_id = <team_id> OR team_b_id = <team_id>` and `ORDER BY played_at ASC`
- [x] 6.3 Write failing test: `result` column is `'win'` when `winner_team_id = team_id` and `'loss'` otherwise
- [x] 6.4 Add `CASE WHEN winner_team_id = <team_id> THEN 'win' ELSE 'loss' END AS result` to the query
- [x] 6.5 Write failing test: `opponent` column resolves correctly whether the team is `team_a` or `team_b`
- [x] 6.6 Add opponent name resolution via a conditional join or `CASE` on `team_a_id`/`team_b_id`

## 7. Match-Tracking Spec Update Verification

- [x] 7.1 Write failing test: ELO update is atomic — partial failure leaves both `winner_team_id` and `elo` unchanged
- [x] 7.2 Confirm `match-tracking` delta spec is consistent with implemented transaction behaviour
