## Context

The Django tournament platform has a complete `core/0001_initial` migration that defines 6 tables, 9 CHECK constraints, 2 UNIQUE constraints, 3 FK-with-RESTRICT rules, 1 FK-with-SET-NULL rule, and 3 performance indexes. Until now the entire test suite runs against SQLite in-memory, which does not enforce CHECK constraints. This change wires up a real PostgreSQL 15+ instance so constraint violations are caught at the database level.

Current state of `settings.py`: hardcoded credentials (`host=localhost`, `user=postgres`, `password=postgres`, `db=tournament_platform`). These cannot be safely committed or shared across machines.

## Goals / Non-Goals

**Goals:**
- Replace hardcoded DB credentials in `settings.py` with environment-variable reads that fail loudly when required vars are absent
- Provide a reproducible local setup path (install PG, create user/db, migrate, verify)
- Ensure `manage.py check --database default` exits 0
- Ensure all 59 existing model tests pass against PostgreSQL (with a separate `pg_settings.py` that uses env vars but targets the real PG instance)

**Non-Goals:**
- Docker / containerized PostgreSQL (out of scope per requirements)
- CI/CD integration
- Staging or production provisioning
- Seeding data

---

## Decisions

### Decision 1: `python-dotenv` over `django-environ`

**Choice:** `python-dotenv` loaded explicitly in `settings.py` via `load_dotenv()`.

**Rationale:** `python-dotenv` has zero Django coupling — it works at the `os.environ` level, keeps `settings.py` idiomatic, and is one dependency smaller than `django-environ`. The `.env` → `os.environ` flow is transparent and testable without Django.

**Alternatives considered:**
- `django-environ`: More ergonomic for complex casting (DB URLs), but overkill for 5 plain string variables.
- Rely on shell exports only: No `.env` support; breaks on fresh checkouts.

---

### Decision 2: Single `settings.py` with env-var reads; `test_settings.py` unchanged

**Choice:** `settings.py` calls `load_dotenv()` and reads `os.environ.get(...)`. `test_settings.py` overrides `DATABASES` with SQLite in-memory as before.

**Rationale:** Unit tests remain fast and offline (SQLite). A separate `pg_settings.py` (inherits from `settings.py`, no override) is used to run the integration test suite against PostgreSQL. This keeps the two test modes orthogonal.

**Alternatives considered:**
- Single settings file with `DATABASE_URL`: Requires `dj-database-url`, adds a dependency.
- Always use PostgreSQL in tests: Slows CI; requires a running PG instance for every test run.

---

### Decision 3: `scripts/setup_db.sh` for reproducible provisioning

**Choice:** Provide a shell script that runs the `psql` commands to DROP/CREATE the database and user, then calls `manage.py migrate`.

**Rationale:** Avoids manual copy-paste from docs. Idempotent (DROP IF EXISTS). No external tools (Ansible, Makefile) required.

**Alternatives considered:**
- `Makefile` target: Extra tooling; `make` not always available on Windows.
- Django management command: Circular — Django can't connect to create its own database.

---

### Decision 4: Fail loudly on missing `DB_USER` / `DB_PASSWORD`

**Choice:** `settings.py` uses `os.environ["DB_USER"]` (raises `KeyError`) for required vars, and `os.environ.get("DB_HOST", "localhost")` for vars with safe defaults.

**Rationale:** Silent fallback to empty credentials would produce a confusing `OperationalError` at connect time. A `KeyError` at settings-load time names the exact missing variable.

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Developer forgets to create `.env` — gets `KeyError` at startup | `.env.example` at project root with clear comments; README setup section |
| `DROP DATABASE` in setup script destroys real data | Script prints a warning and requires `--confirm-drop` flag when `DB_NAME` is not `tournament_platform` |
| PostgreSQL 14 installed silently — CHECK constraints with OR-logic may behave differently | Script checks `SELECT version()` and aborts if < 15 |
| `test_settings.py` still uses SQLite — CHECK constraints not tested in unit tests | Integration test target (`pg_settings.py`) runs the same 59 tests against PG; both suites must pass |

## Migration Plan

1. Add `python-dotenv` to `requirements/requirements.txt`
2. Update `settings.py`: add `load_dotenv()`, replace hardcoded `DATABASES` values
3. Create `pg_settings.py` (inherits from `settings.py`, no DB override)
4. Create `.env.example` and update `.gitignore`
5. Create `scripts/setup_db.sh`
6. Run `scripts/setup_db.sh` → `python manage.py migrate`
7. Run `pytest tests/ --ds=tournament_platform.pg_settings` — all 59 must pass
8. Run `python manage.py check --database default`

**Rollback:** Revert `settings.py` to hardcoded values; drop the database with `dropdb tournament_platform`.

## Open Questions

- Resolved: `python-dotenv` selected (see Decision 1).
