## 1. Dependencies & Environment Config

- [x] 1.1 Add `python-dotenv` to `requirements/requirements.txt`
- [x] 1.2 Install updated requirements in the virtual environment (`uv pip install -r requirements/requirements.txt`)
- [x] 1.3 Update `django-api/app/tournament_platform/settings.py`: add `load_dotenv()` call and replace hardcoded `DATABASES` values with `os.environ` reads (required: `DB_USER`, `DB_PASSWORD`; optional with defaults: `DB_NAME`, `DB_HOST`, `DB_PORT`)
- [x] 1.4 Create `django-api/app/tournament_platform/pg_settings.py` that imports `from tournament_platform.settings import *` with no `DATABASES` override
- [x] 1.5 Create `.env.example` at the project root (`django-api/`) with all five variables and inline comments
- [x] 1.6 Add `.env` to `django-api/.gitignore` (create `.gitignore` if absent)

## 2. Failing Tests for env-config

- [x] 2.1 Write failing test: `DB_USER` absent → `KeyError` raised at settings import (use `importlib.reload` or `pytest.raises`)
- [x] 2.2 Write failing test: `DB_PASSWORD` absent → `KeyError` raised at settings import
- [x] 2.3 Write failing test: optional vars absent → defaults (`tournament_platform`, `localhost`, `5432`) applied
- [x] 2.4 Write failing test: `.env.example` contains exactly the keys `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- [x] 2.5 Write failing test: `pg_settings` imports without error and does not override `DATABASES`

## 3. PostgreSQL Installation & Provisioning Script

- [x] 3.1 Write failing test: `scripts/setup_db.sh` exists and is executable
- [x] 3.2 Write failing test: script aborts with exit code 1 when PostgreSQL < 15 is detected (mock `psql --version` output)
- [x] 3.3 Create `django-api/scripts/setup_db.sh`:
  - Check `psql --version` ≥ 15; abort with message if not
  - `CREATE ROLE IF NOT EXISTS $DB_USER LOGIN CREATEDB PASSWORD '$DB_PASSWORD'`
  - `DROP DATABASE IF EXISTS $DB_NAME; CREATE DATABASE $DB_NAME OWNER $DB_USER`
  - Run `python app/manage.py migrate`
- [x] 3.4 Make `setup_db.sh` executable (`chmod +x`)

## 4. Verification Tests (PostgreSQL-level)

- [x] 4.1 Write failing integration test: after migration, query `information_schema.tables` and assert all 6 domain tables are present (requires live PG — mark with `@pytest.mark.integration`)
- [x] 4.2 Write failing integration test: query `information_schema.table_constraints` and assert the 7 CHECK constraints and 2 UNIQUE constraints are present
- [x] 4.3 Write failing integration test: query `pg_indexes` and assert `users_elo_desc_idx`, `matches_tournament_idx`, `matches_played_at_idx` exist
- [x] 4.4 Write failing integration test: raw SQL INSERT with invalid `winner_team_id` raises `IntegrityError` with constraint name `matches_winner_valid`

## 5. Run Migration & Full Verification

- [ ] 5.1 Run `scripts/setup_db.sh` with a live PostgreSQL ≥ 15 instance and confirm exit 0
- [ ] 5.2 Run `python app/manage.py check --database default` and confirm exit 0
- [ ] 5.3 Run `pytest tests/ --ds=tournament_platform.pg_settings -q` and confirm 59 tests pass
- [ ] 5.4 Run integration tests (`pytest tests/ -m integration --ds=tournament_platform.pg_settings`) and confirm all pass
- [ ] 5.5 Run `pytest tests/ -q` (SQLite / `test_settings`) and confirm 59 tests still pass (no regression)
