## Why

The tournament platform needs a normalized relational database foundation to persist users, teams, tournaments, and match results before any feature work can begin. Without this schema and the Django REST API skeleton, no other service can store or query competitive data.

## What Changes

- Introduce six database tables: `users`, `teams`, `team_members`, `tournaments`, `tournament_teams`, `matches`
- Add all foreign keys, check constraints, composite primary keys, and performance indexes as specified
- Create Django models, initial migrations, serializers, and a router-registered API skeleton
- Provide an entity-relationship diagram (Mermaid) documenting table relationships

## Capabilities

### New Capabilities

- `user-management`: User accounts with ELO ranking, role enforcement (`admin`/`player`), and uniqueness constraints
- `team-management`: Team creation with owner FK, team membership via junction table
- `tournament-management`: Tournament lifecycle tracking (`draft` → `open` → `ongoing` → `finished`) with format and date constraints
- `match-tracking`: Match records linking two teams within a tournament, winner validation via CHECK constraint, and score recording

### Modified Capabilities

<!-- none — this is the initial schema -->

## Impact

- **New Django app(s)**: models, serializers, URLs/router wiring, and migrations
- **Database**: PostgreSQL schema with indexes on `users.elo`, `matches.tournament_id`, and `matches.played_at`
- **Dependencies**: Django, Django REST Framework, psycopg2 (or psycopg3)
- **Out of scope**: auth endpoints, ELO recalculation logic, bracket generation, frontend, deployment
