## Context

The project is a Django REST Framework tournament platform. All business logic currently lives in a single `core` app under `django-api/app/core/`, with configuration in `app/tournament_platform/`. The codebase has a complete test suite and a single Alembic-style Django migration (`core/migrations/0001_initial.py`). The goal is a structural reorganisation — no logic, API behaviour, or schema changes.

Key constraints from the requirements spec:
- `AUTH_USER_MODEL` must change from `'core.User'` to `'users.User'`
- The existing migration must be split into three per-app migrations preserving FK dependency order
- All imports referencing `core` or `tournament_platform` must be updated
- Tests must remain fully green after the migration

## Goals / Non-Goals

**Goals:**
- Produce the exact directory tree specified in `requirements/folder-structure.md`
- Zero test regressions — `pytest` passes with the same count and results
- No `core` or `tournament_platform` module references remain in any Python file
- `python manage.py check` passes for development and testing settings
- Migrations split cleanly with correct `app_label` and `dependencies`

**Non-Goals:**
- Changing any business logic, validation, or API behaviour
- Adding new models, endpoints, or serializer fields
- Modifying Docker, CI/CD, or deployment configuration
- Changing dependency versions
- Updating `mutants/` directory (auto-generated)

## Decisions

### D1: Migration split strategy — three separate initial migrations
**Decision**: Split `core/0001_initial.py` into three per-app migrations (`users`, `teams`, `tournaments`) rather than keeping a single migration in one app.

**Rationale**: Aligns each migration with its owning app, avoids cross-app `CreateModel` in a foreign app label, and establishes clean dependency edges (`teams` depends on `users`; `tournaments` depends on both). The original monolithic migration is deleted entirely.

**Alternative considered**: Place entire migration in `apps/users/` with `app_label = 'users'` and reference all models there. Rejected because it violates single-responsibility — teams and tournaments models would be created under the wrong app label.

### D2: FK string references — use `settings.AUTH_USER_MODEL` for User FK, string paths for others
**Decision**: All FK fields pointing to `User` use `settings.AUTH_USER_MODEL`. FK fields pointing to `Team` use `'teams.Team'` string notation.

**Rationale**: Avoids circular imports across app packages. Django resolves lazy string references at startup. `settings.AUTH_USER_MODEL` is the canonical pattern for FK-to-custom-user-model.

### D3: Settings split — shared base, thin environment overrides
**Decision**: `base.py` holds all shared settings. `development.py`, `testing.py`, `production.py` each start with `from .base import *` and only declare environment-specific overrides. No setting is duplicated.

**Rationale**: Matches the requirements spec exactly. Ensures `testing.py` contains all overrides from the existing `test_settings.py` (test DB name, password hashers, disabled throttling).

### D4: AppConfig — full dotted path in INSTALLED_APPS
**Decision**: `INSTALLED_APPS` uses full `AppConfig` paths: `'apps.users.apps.UsersConfig'`, `'apps.teams.apps.TeamsConfig'`, `'apps.tournaments.apps.TournamentsConfig'`.

**Rationale**: Explicit `AppConfig` references are the current Django best practice, unambiguous, and avoid relying on `default_app_config` (deprecated in Django 3.2+).

### D5: Test reorganisation — mirror app structure, keep single conftest
**Decision**: Move test files to `tests/users/`, `tests/teams/`, `tests/tournaments/`. Keep `tests/conftest.py` at root with all shared fixtures.

**Rationale**: Matches the target tree. Root-level `conftest.py` is automatically discovered by pytest for all sub-packages.

## Risks / Trade-offs

- **AUTH_USER_MODEL rename** → If a live database exists, the `users_user` table name differs from `core_user`. Mitigation: this is a fresh-install project; document the change clearly. For live databases, a separate `SeparateDatabaseAndState` migration would be needed (out of scope per requirements).
- **Migration split correctness** → If FK dependencies in the split migrations don't match exactly, `migrate` will fail. Mitigation: verify with `python manage.py migrate --run-syncdb` on a blank database after the split.
- **Import churn** → Large number of import updates increases risk of a missed reference. Mitigation: after migration, run `grep -r "from core\|import core\|from tournament_platform\|import tournament_platform" app/ tests/` to confirm zero matches.
- **pg_settings.py** → This file exists in `tournament_platform/` but has no counterpart in the target tree. Per the requirements open question, its content should be merged into `config/settings/base.py` or `production.py`. Decision: merge into `base.py` if settings are shared, `production.py` if production-only.

## Migration Plan

1. Create target directory structure (empty `__init__.py` files, `apps.py` per app)
2. Split models → per-app `models.py`
3. Split serializers → per-app `serializers/input.py` and `serializers/output.py`
4. Split views and URLs → per-app `views.py` and `urls.py`
5. Move admin, authentication, sql_queries, management commands
6. Create `common/exceptions.py`, `common/pagination.py`, `common/permissions.py`
7. Create `config/` package with split settings and updated `urls.py`, `asgi.py`, `wsgi.py`
8. Write three per-app initial migrations
9. Update `manage.py`, `pytest.ini`, `setup.cfg`, `mutmut_config.py`
10. Update all imports across source and test files
11. Reorganise test files
12. Verify: `python manage.py check`, `pytest`, grep for stale imports

**Rollback**: Git branch — entire migration is on `feature/estructura`; reverting the branch restores the monolithic structure.

## Open Questions

- **pg_settings.py content**: Should its settings merge into `base.py` or `production.py`? (Needs review of file contents before placement.)
- **Live database**: Confirm no production database exists before proceeding — if one does, `AUTH_USER_MODEL` rename requires additional migration steps.
