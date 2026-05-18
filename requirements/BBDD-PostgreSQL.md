# Requirements: Tournament Platform — PostgreSQL Database Setup & Migration

## Purpose
Install and configure a local PostgreSQL ≥ 15 instance, create the `tournament_platform` database, and apply all Django migrations to produce the complete schema (6 tables, constraints, indexes). This unblocks task 6.2 and enables running the full test suite against a real relational database instead of SQLite in-memory.

## Scope
- **In scope:**
  - Installation of PostgreSQL ≥ 15 on the developer's local machine
  - Creation of a single PostgreSQL user with full privileges on the target database
  - Creation of the `tournament_platform` database (DROP + CREATE if it already exists)
  - Django settings updated to read connection credentials from environment variables
  - Running `python manage.py migrate` to apply `0001_initial` and all subsequent migrations
  - Verification: 6 tables present, CHECK constraints and indexes present, `manage.py check --database default` exits 0, and model tests pass against PostgreSQL
- **Out of scope:**
  - CI/CD pipeline integration
  - Staging or production database provisioning
  - Seed data or fixtures
  - High-availability, replication, or backup configuration
  - SSL/TLS configuration for the database connection
  - Multiple database users with separate permission scopes

---

## Requirements

1. PostgreSQL version 15 or higher MUST be installed on the local machine before any subsequent steps are executed.

2. A single PostgreSQL user (role) MUST be created with `LOGIN`, `CREATEDB`, and full privileges on the `tournament_platform` database. Username and password are supplied via environment variables `DB_USER` and `DB_PASSWORD`.

3. If a database named `tournament_platform` already exists at setup time, it MUST be dropped entirely (`DROP DATABASE`) before being recreated (`CREATE DATABASE`). No confirmation prompt is required.

4. The database MUST be owned by the user created in requirement 2.

5. Django's `settings.py` MUST read all connection parameters exclusively from environment variables:

   | Setting      | Environment Variable | Default if unset |
   |--------------|----------------------|------------------|
   | `NAME`       | `DB_NAME`            | `tournament_platform` |
   | `USER`       | `DB_USER`            | *(no default — fail loudly)* |
   | `PASSWORD`   | `DB_PASSWORD`        | *(no default — fail loudly)* |
   | `HOST`       | `DB_HOST`            | `localhost` |
   | `PORT`       | `DB_PORT`            | `5432` |

6. A `.env.example` file MUST be provided at the project root listing all five variables with placeholder values. A `.env` file MUST be listed in `.gitignore`.

7. `python manage.py migrate` MUST apply migration `core/0001_initial` without errors and produce exactly the following tables: `users`, `teams`, `team_members`, `tournaments`, `tournament_teams`, `matches`.

8. After migration, the database MUST contain all constraints and indexes specified in the schema design:
   - `CHECK` constraints: `users_role_valid`, `tournaments_status_valid`, `tournaments_format_valid`, `tournaments_max_teams_positive`, `tournaments_end_date_gte_start_date`, `matches_status_valid`, `matches_winner_valid`
   - `UNIQUE` constraints: `team_members_pk`, `tournament_teams_pk`
   - `FOREIGN KEY` rules: `ON DELETE RESTRICT` on all FKs except `matches.winner_team_id` which is `ON DELETE SET NULL`
   - Indexes: `users_elo_desc_idx` (DESC), `matches_tournament_idx`, `matches_played_at_idx`

9. `python manage.py check --database default` MUST exit with code 0 after migration.

10. The model test suite (`pytest tests/`) MUST pass in full when `DJANGO_SETTINGS_MODULE` points to the production settings (not `test_settings`) and a live PostgreSQL instance is available. All 59 tests MUST pass.

---

## Scenarios

### Fresh Install — Happy Path
- GIVEN PostgreSQL 15 is not installed and the environment variables are set in `.env`
- WHEN the developer follows the setup steps (install PG, create user/DB, run migrate)
- THEN `python manage.py check --database default` exits 0 and `pytest tests/` reports 59 passed

### Database Already Exists
- GIVEN a `tournament_platform` database already exists with data
- WHEN the setup script is run again
- THEN the existing database is dropped, recreated empty, and migrations are applied from scratch without any manual intervention

### Missing Environment Variable
- GIVEN `DB_USER` or `DB_PASSWORD` is not set in the environment
- WHEN `python manage.py migrate` is executed
- THEN Django raises `ImproperlyConfigured` (or equivalent) with a message identifying the missing variable; no partial migration is applied

### Wrong PostgreSQL Version
- GIVEN PostgreSQL 14 or earlier is installed
- WHEN `python manage.py migrate` is executed
- THEN the process fails with an explicit version error before any DDL is applied

### Migration Already Applied
- GIVEN all migrations have already been applied to the database
- WHEN `python manage.py migrate` is run again
- THEN Django reports "No migrations to apply." and exits 0; no tables are dropped or altered

### Constraint Enforcement Verified
- GIVEN migrations have been applied
- WHEN a raw SQL `INSERT INTO matches (..., winner_team_id) VALUES (..., <id not in team_a or team_b>)` is executed
- THEN PostgreSQL raises a `CHECK constraint "matches_winner_valid" violation` error

---

## Open Questions

- **Python-dotenv or django-environ?** The requirement mandates reading from environment variables but does not specify the library for loading `.env` files. Recommend `python-dotenv` for simplicity; confirm before implementation.
