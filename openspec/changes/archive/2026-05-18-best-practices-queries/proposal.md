## Why

The team needs to validate and understand the exact SQL semantics the tournament platform
relies on before delegating query generation to Django ORM. Writing and running raw SQL
first in `psql` surfaces slow plans, missing indexes, and subtle join behaviour that ORM
abstraction would otherwise hide until production.

## What Changes

- Add a B-tree index `idx_users_elo` on `users(elo)` to support fast leaderboard lookups.
- Write and document five canonical SQL queries: leaderboard ranking, team win aggregation,
  dual-alias match listing, transactional ELO update, and per-team match history.
- Provide a reusable transaction block (compatible with `psql` substitution) for
  match-result reporting with automatic rollback on failure.

## Capabilities

### New Capabilities

- `sql-queries`: Raw SQL queries for the tournament platform — leaderboard ranking with index,
  team win counts (all-time and per-tournament), match listing with dual team-name resolution,
  transactional match-result reporting with Elo K=32 recalculation, and chronological team
  match history with win/loss result column.

### Modified Capabilities

- `match-tracking`: ELO recalculation logic (K=32 standard formula) is now specified as a
  requirement — previously unspecified at the spec level.

## Impact

- **Database:** One new index on `users(elo)`; no schema changes.
- **match-tracking spec:** ELO update formula becomes a documented, testable requirement.
- **No Django ORM changes** in this phase — queries are validated in `psql` only.
- **No API or endpoint changes.**
