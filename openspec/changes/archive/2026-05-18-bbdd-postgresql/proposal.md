## Why

The Django application has a complete schema and migrations, but no PostgreSQL instance exists locally — all tests run against SQLite in-memory. This change provisions the real database so that CHECK constraints, FK rules, and indexes are enforced at the engine level and the full test suite passes against production-equivalent infrastructure.

## What Changes

- Install PostgreSQL ≥ 15 on the developer's local machine
- Create a dedicated PostgreSQL user with full privileges on the target database
- Create the `tournament_platform` database (DROP + CREATE if already exists)
- **BREAKING** (settings): `settings.py` is updated to read all connection parameters from environment variables — hardcoded `postgres/postgres` credentials are removed
- Add `.env.example` listing the five required variables; add `.env` to `.gitignore`
- Run `python manage.py migrate` to apply `core/0001_initial` against the live PostgreSQL instance
- Verify schema completeness: 6 tables, all constraints, all indexes, `manage.py check` passes, and 59 model tests pass against PostgreSQL

## Capabilities

### New Capabilities

- `postgresql-setup`: Installing PostgreSQL ≥ 15, creating the user and database, and verifying the instance is reachable from Django
- `env-config`: Reading all database connection parameters from environment variables with explicit failure when required variables are absent

### Modified Capabilities

- `user-management`: No requirement change — `users` table now enforced by PostgreSQL CHECK constraints instead of SQLite (behavioral parity, not spec change)

## Impact

- **`django-api/app/tournament_platform/settings.py`**: `DATABASES` block changes from hardcoded values to `os.environ.get(...)` calls
- **`django-api/app/tournament_platform/test_settings.py`**: Remains SQLite in-memory for unit tests; unaffected
- **New files**: `.env.example`, `.env` (gitignored), optionally a `scripts/setup_db.sh` helper
- **Dependencies added**: `python-dotenv` (or `django-environ`) to load `.env` files
- **`requirements/requirements.txt`**: Updated with the chosen env-loading library
