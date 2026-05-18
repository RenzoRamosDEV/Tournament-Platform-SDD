# Requirements: Advanced SQL Query Practice for Tournament Platform

## Purpose

Develop and validate a set of production-quality raw SQL queries against the tournament
platform's PostgreSQL database before integrating them into Django ORM. Mastering the SQL
layer first allows the developer to detect slow query plans, verify index usage, and
understand the exact semantics that Django ORM will later generate.

## Scope

- **In scope:**
  - Five specific SQL queries covering ranking, aggregation, multi-table joins, transactional
    updates, and chronological history
  - Index definition for the `elo` column on the `users` table
  - A PostgreSQL transaction block for match-result reporting including ELO recalculation
  - Direct execution and verification in `psql` before any Django ORM integration

- **Out of scope:**
  - Django ORM equivalents or migrations (separate task)
  - Any write operations other than the transaction in Requirement 4
  - Pagination beyond the explicit LIMIT 50 in Requirement 1
  - Tournament brackets, seeding logic, or scheduling

---

## Data Model Assumptions

The following table and column names are assumed to exist:

| Table     | Relevant columns                                                         |
|-----------|--------------------------------------------------------------------------|
| `users`   | `id`, `username`, `elo`                                                  |
| `teams`   | `id`, `name`                                                             |
| `matches` | `id`, `tournament_id`, `team_a_id`, `team_b_id`, `winner_id`, `played_at` |

Matches never end in a draw: `winner_id` is always either `team_a_id` or `team_b_id`.

---

## Requirements

1. **Ranking query with index support**
   A B-tree index named `idx_users_elo` must exist on `users(elo)`. The ranking query
   must select `username` and `elo` from `users`, order results by `elo` descending, and
   return exactly the top 50 rows. The query must use the index (confirmed via `EXPLAIN ANALYZE`
   showing "Index Scan" or "Index Only Scan" on `idx_users_elo`).

2. **Teams with most wins — all-time and per-tournament**
   The primary query must join `teams` and `matches`, group by `teams.id` and `teams.name`,
   count rows where `matches.winner_id = teams.id`, and order by win count descending.
   A secondary variant must add a `WHERE matches.tournament_id = :tournament_id` filter
   so wins can be scoped to a single tournament. Both variants must use `GROUP BY` and
   return `team_name` and `win_count` columns.

3. **Tournament matches with dual team name resolution**
   The query must return every row from `matches` together with the resolved name of each
   participant. `matches` must be joined to `teams` twice: once aliased as `team_a` on
   `team_a_id = team_a.id`, and once aliased as `team_b` on `team_b_id = team_b.id`.
   The result columns must include `match_id`, `team_a_name`, `team_b_name`, `winner_id`,
   and `played_at`.

4. **Transactional match-result reporting with ELO recalculation**
   When a match result is recorded, the following operations must execute inside a single
   `BEGIN … COMMIT` block:

   a. Set `matches.winner_id` to the winning team's `id` for the given `match_id`.

   b. Recalculate ELO for **both** participating users using the standard Elo formula with
      K = 32:
      ```
      expected_score = 1 / (1 + 10 ^ ((opponent_elo - player_elo) / 400))
      new_elo = old_elo + 32 * (actual_result - expected_score)
      ```
      where `actual_result` = 1 for the winner and 0 for the loser.
      ELO values must be updated with `UPDATE users SET elo = <new_value> WHERE id = <user_id>`.

   c. If any statement within the block raises an error, the entire transaction must be
      rolled back via `ROLLBACK`, leaving all rows unchanged.

   The transaction must be written so it can be executed verbatim in `psql` with substituted
   parameters.

5. **Team match history ordered by date**
   Given a specific `:team_id`, the query must return all matches in which that team
   participated (`team_a_id = :team_id OR team_b_id = :team_id`), ordered by `played_at`
   ascending. Each row must include `match_id`, `played_at`, the opposing team's `name`
   aliased as `opponent`, and a computed `result` column that reads `'win'` when
   `winner_id = :team_id` and `'loss'` otherwise, derived with a `CASE` expression.

---

## Scenarios

### Ranking query uses the declared index
- GIVEN the `idx_users_elo` index exists on `users(elo)`
- WHEN `EXPLAIN ANALYZE` is run on the ranking query
- THEN the query plan contains "Index Scan" or "Index Only Scan" on `idx_users_elo` and
  returns exactly 50 rows

### All-time win count includes every tournament
- GIVEN teams A, B, C have 10, 7, and 3 wins across two different tournaments
- WHEN the all-time wins query is executed
- THEN the result is ordered A (10), B (7), C (3) with no tournament filter applied

### Per-tournament win count excludes other tournaments
- GIVEN team A has 6 wins in tournament 1 and 4 wins in tournament 2
- WHEN the per-tournament variant is executed with `tournament_id = 1`
- THEN team A appears with `win_count = 6`, and its tournament-2 wins are not counted

### Match query resolves both team names
- GIVEN a match where `team_a_id = 1` ("Dragons") and `team_b_id = 2` ("Phoenix")
- WHEN the tournament matches query is executed
- THEN the row contains `team_a_name = 'Dragons'` and `team_b_name = 'Phoenix'`

### Transaction commits all updates on success
- GIVEN a valid match between user A (elo=1200) and user B (elo=1000), user A wins
- WHEN the transaction block is executed without errors
- THEN `matches.winner_id` is set, user A's elo increases, user B's elo decreases,
  and both changes persist after `COMMIT`

### Transaction rolls back entirely on error
- GIVEN the transaction block encounters an error on the second UPDATE statement
- WHEN `ROLLBACK` is executed
- THEN `matches.winner_id` remains NULL and both users' elo values are unchanged

### Team history shows chronological win/loss
- GIVEN team X played three matches: lost on 2025-01-01, won on 2025-02-01, won on 2025-03-01
- WHEN the team history query is executed for team X
- THEN results are returned in that date order with `result` values `'loss'`, `'win'`, `'win'`
