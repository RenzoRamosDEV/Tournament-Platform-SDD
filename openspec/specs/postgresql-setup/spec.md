## ADDED Requirements

### Requirement: PostgreSQL version enforcement
The system SHALL verify that the installed PostgreSQL version is 15 or higher before executing any database provisioning steps. If the version requirement is not met, the setup process MUST abort with an explicit message stating the installed version and the minimum required version.

#### Scenario: Version check passes
- **WHEN** PostgreSQL 15 or higher is installed and `setup_db.sh` is run
- **THEN** the script continues to the database provisioning steps without error

#### Scenario: Version check fails
- **WHEN** PostgreSQL 14 or earlier is installed and `setup_db.sh` is run
- **THEN** the script exits with code 1 and prints: `ERROR: PostgreSQL >= 15 required, found <version>`

---

### Requirement: Database user provisioning
The system SHALL create a PostgreSQL role with `LOGIN` and `CREATEDB` privileges using the credentials supplied by `DB_USER` and `DB_PASSWORD` environment variables. If the role already exists, the provisioning step MUST be skipped without error.

#### Scenario: User created successfully
- **WHEN** `DB_USER` and `DB_PASSWORD` are set and the role does not yet exist
- **THEN** a PostgreSQL role is created with `LOGIN CREATEDB` and the script proceeds

#### Scenario: User already exists
- **WHEN** the role named `DB_USER` already exists in PostgreSQL
- **THEN** the creation step is skipped and the script continues without error

---

### Requirement: Database creation with DROP-and-recreate
The system SHALL drop the existing database (if any) and create a fresh one owned by `DB_USER`. The database name is taken from `DB_NAME` (default: `tournament_platform`). No interactive confirmation is required.

#### Scenario: Fresh database creation
- **WHEN** no database named `DB_NAME` exists
- **THEN** the database is created and owned by `DB_USER`

#### Scenario: Existing database dropped and recreated
- **WHEN** a database named `DB_NAME` already exists
- **THEN** it is dropped and recreated empty, owned by `DB_USER`

---

### Requirement: Migration execution and schema verification
The system SHALL run `python manage.py migrate` and verify that exactly the 6 domain tables are present, all CHECK constraints are active, and all indexes exist after migration completes.

#### Scenario: Migration runs without errors
- **WHEN** `python manage.py migrate` is executed against a clean `tournament_platform` database
- **THEN** the command exits 0 and reports that `core/0001_initial` was applied

#### Scenario: Django connectivity check passes
- **WHEN** `python manage.py check --database default` is run after migration
- **THEN** it exits 0 with no errors or warnings

#### Scenario: All 6 tables present after migration
- **WHEN** migration completes
- **THEN** a `\dt` query in `psql` returns exactly: `users`, `teams`, `team_members`, `tournaments`, `tournament_teams`, `matches`

#### Scenario: CHECK constraint enforced by PostgreSQL
- **WHEN** a raw SQL `INSERT INTO matches` sets `winner_team_id` to a team not participating in the match
- **THEN** PostgreSQL raises `ERROR: new row for relation "matches" violates check constraint "matches_winner_valid"`

#### Scenario: Idempotent re-migration
- **WHEN** `python manage.py migrate` is run a second time on an already-migrated database
- **THEN** it exits 0 and prints `No migrations to apply.`

---

### Requirement: Integration test suite passes against PostgreSQL
All 59 model tests MUST pass when executed with `DJANGO_SETTINGS_MODULE=tournament_platform.pg_settings` against a live PostgreSQL instance.

#### Scenario: Full test suite passes on PostgreSQL
- **WHEN** `pytest tests/ --ds=tournament_platform.pg_settings` is run with a running PostgreSQL instance
- **THEN** 59 tests pass and 0 fail
