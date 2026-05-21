## Why

The project currently lives in a single monolithic `core` app, which conflates user, team, and tournament domain logic into one package. Splitting it into three domain apps (`users`, `teams`, `tournaments`) with shared utilities in `common/` and a proper `config/` package will isolate domain concerns, simplify future maintenance, and align the codebase with conventional Django project layout.

## What Changes

- Split `app/core/` into three domain apps: `apps/users/`, `apps/teams/`, `apps/tournaments/`
- Move shared utilities (`exceptions.py`, `pagination.py`) to `app/common/`; create `common/permissions.py`
- Rename config package from `app/tournament_platform/` to `app/config/`
- Split monolithic `settings.py` into `config/settings/base.py`, `development.py`, `testing.py`, `production.py`
- Split the single `core/migrations/0001_initial.py` into three per-app initial migrations, each with the correct `app_label` and cross-app `dependencies`
- Move per-domain models, serializers (input/output), views, URLs, admin, and management commands to their respective app packages
- Move `authentication.py` → `apps/users/authentication.py`; `sql_queries.py` → `apps/tournaments/sql_queries.py`
- Reorganise `tests/core/` into `tests/users/`, `tests/teams/`, `tests/tournaments/` mirroring the new app structure
- Update all imports, `INSTALLED_APPS`, `DJANGO_SETTINGS_MODULE`, `manage.py` default settings, and `mutmut_config.py` paths
- **BREAKING**: `AUTH_USER_MODEL` changes from `'core.User'` to `'users.User'` (affects fresh installs; live databases require data migration consideration)

## Capabilities

### New Capabilities

- `django-app-structure`: Domain-separated Django app layout with `apps/users`, `apps/teams`, `apps/tournaments`, shared `common/` utilities, and a `config/` settings package replacing the monolithic `core` and `tournament_platform` packages.

### Modified Capabilities

<!-- No existing spec-level capabilities are changing — this is a structural reorganisation with no business logic or API behaviour changes. -->

## Impact

- **Source files**: Every Python file under `app/core/` and `app/tournament_platform/` is moved or split; all internal imports updated.
- **Migrations**: `core` app label disappears; three new per-app migrations replace the single `core/0001_initial.py`.
- **Settings**: `DJANGO_SETTINGS_MODULE` env var consumers (Docker, CI, shell) must point to `config.settings.<env>`.
- **Tests**: All test files under `tests/core/` are relocated; `conftest.py` fixtures must continue to resolve for all new packages.
- **mutmut**: `paths_to_mutate` updated from `app/core/` to `app/apps/` and `app/common/`.
- **No API behaviour changes**: URL prefixes, endpoint logic, serializer fields, and query logic are preserved exactly.
