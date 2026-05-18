## Context

The tournament platform stores users, teams, matches, and tournaments in PostgreSQL.
Query logic currently lives only in Django ORM. Before any ORM integration, five
canonical queries must be validated directly in `psql` to confirm index usage, correct
join behaviour, and transaction semantics. The ELO formula (K=32) has never been
formally documented at the spec level.

## Goals / Non-Goals

**Goals:**
- Define the exact SQL for each of the five queries so they can be run, inspected with
  `EXPLAIN ANALYZE`, and replicated as tests.
- Add a single B-tree index on `users(elo)` and confirm it is used by the ranking query.
- Specify the ELO recalculation transaction as a self-contained `psql`-executable block.
- Promote the ELO formula into the `match-tracking` spec as a normative requirement.

**Non-Goals:**
- Django ORM translation (separate task).
- Schema migrations beyond the one index.
- Query optimisation beyond confirming index use.

## Decisions

### 1. B-tree index on `users(elo)`, not a covering index
A plain B-tree on `elo` is sufficient for `ORDER BY elo DESC LIMIT 50`. A covering index
(`INCLUDE (username)`) would allow an Index Only Scan but adds write overhead for a column
that changes frequently. Plain index chosen; upgrade to covering index if profiling shows
heap fetches as the bottleneck.

### 2. ELO recalculation as raw SQL inside the transaction, not a PL/pgSQL function
The transaction block uses inline arithmetic (`1.0 / (1 + power(10, (opp_elo - my_elo) /
400.0))`) rather than a stored function. Rationale: keeps the query self-contained and
portable to Django ORM without requiring a function migration. A stored function can be
added later if the formula needs to be called from multiple places.

### 3. Team history uses `CASE` expression, not a view
The `result` column is computed inline with `CASE WHEN winner_id = :team_id THEN 'win'
ELSE 'loss' END`. No view is introduced to keep the query standalone and auditable.

### 4. `winner_id` column name in queries vs. `winner_team_id` in spec
The existing `match-tracking` spec names the column `winner_team_id`. The requirements
file uses `winner_id`. The delta spec for `match-tracking` does not rename this column —
the discrepancy is resolved by using the canonical spec name (`winner_team_id`) in all
five queries and treating `winner_id` in the requirements file as a shorthand alias.

## Risks / Trade-offs

- **Index not used on small datasets** → PostgreSQL may prefer a sequential scan if
  the `users` table has fewer than a few hundred rows during development. Use
  `SET enable_seqscan = off` in `psql` to force index use for plan verification only.
- **ELO arithmetic precision** → Integer `elo` column truncates fractional gains.
  The formula must cast to `NUMERIC` before rounding back to `INTEGER` on update.
  Mitigation: use `ROUND(... ::NUMERIC)::INTEGER` in the UPDATE statement.
- **Transaction parameter substitution in psql** → `psql` uses `\set var value` for
  variables. The block must document this convention so it can be pasted and run without
  modification.
