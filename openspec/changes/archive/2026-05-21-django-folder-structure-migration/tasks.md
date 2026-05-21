## 1. Create Target Directory Skeleton

- [x] 1.1 Create `app/apps/__init__.py`
- [x] 1.2 Create `app/apps/users/` with `__init__.py`, `apps.py` (`name = 'apps.users'`)
- [x] 1.3 Create `app/apps/teams/` with `__init__.py`, `apps.py` (`name = 'apps.teams'`)
- [x] 1.4 Create `app/apps/tournaments/` with `__init__.py`, `apps.py` (`name = 'apps.tournaments'`)
- [x] 1.5 Create `app/common/` with `__init__.py`
- [x] 1.6 Create `app/config/` with `__init__.py` and `app/config/settings/` with `__init__.py`
- [x] 1.7 Create per-app `serializers/` packages (`__init__.py` in each)
- [x] 1.8 Create per-app `migrations/` packages (`__init__.py` in each)
- [x] 1.9 Create `app/apps/users/management/__init__.py` and `commands/__init__.py`

## 2. Split Models

- [x] 2.1 Create `app/apps/users/models.py` with `User` and `EloHistory` (FK to self via `settings.AUTH_USER_MODEL` where needed)
- [x] 2.2 Create `app/apps/teams/models.py` with `Team` and `TeamMember` (FK to `settings.AUTH_USER_MODEL`)
- [x] 2.3 Create `app/apps/tournaments/models.py` with `Tournament`, `TournamentTeam`, `Match` (FK to `'teams.Team'` and `settings.AUTH_USER_MODEL`)
- [x] 2.4 Update `AUTH_USER_MODEL` in settings from `'core.User'` to `'users.User'`

## 3. Split Serializers

- [x] 3.1 Create `app/apps/users/serializers/input.py` and `output.py` with user-related serializers
- [x] 3.2 Create `app/apps/teams/serializers/input.py` and `output.py` with team-related serializers
- [x] 3.3 Create `app/apps/tournaments/serializers/input.py` and `output.py` with tournament-related serializers

## 4. Split Views and URLs

- [x] 4.1 Create `app/apps/users/views.py` with user-related views
- [x] 4.2 Create `app/apps/teams/views.py` with team-related views
- [x] 4.3 Create `app/apps/tournaments/views.py` with tournament-related views
- [x] 4.4 Create `app/apps/users/urls.py` with user URL patterns
- [x] 4.5 Create `app/apps/teams/urls.py` with team URL patterns
- [x] 4.6 Create `app/apps/tournaments/urls.py` with tournament URL patterns

## 5. Move Remaining App Files

- [x] 5.1 Create `app/apps/users/admin.py` with user and elo history admin registrations
- [x] 5.2 Create `app/apps/teams/admin.py` with team and team member admin registrations
- [x] 5.3 Create `app/apps/tournaments/admin.py` with tournament-related admin registrations
- [x] 5.4 Move `core/authentication.py` → `app/apps/users/authentication.py` (update imports)
- [x] 5.5 Move `core/sql_queries.py` → `app/apps/tournaments/sql_queries.py` (update imports)
- [x] 5.6 Move `core/management/commands/seed_data.py` → `app/apps/users/management/commands/seed_data.py` (update imports)

## 6. Create common Package

- [x] 6.1 Create `app/common/exceptions.py` with content from `core/exceptions.py` (updated imports)
- [x] 6.2 Create `app/common/pagination.py` with content from `core/pagination.py` (updated imports)
- [x] 6.3 Create `app/common/permissions.py` with any permission classes from `core/` (or empty module)

## 7. Create config Package and Split Settings

- [x] 7.1 Review `tournament_platform/pg_settings.py` and merge content into `config/settings/base.py` or `production.py`
- [x] 7.2 Create `config/settings/base.py` with all shared settings (update `INSTALLED_APPS`, `AUTH_USER_MODEL`)
- [x] 7.3 Create `config/settings/development.py` (`from .base import *` + dev overrides)
- [x] 7.4 Create `config/settings/testing.py` (`from .base import *` + all overrides from `test_settings.py`)
- [x] 7.5 Create `config/settings/production.py` (`from .base import *` + production overrides)
- [x] 7.6 Move `tournament_platform/urls.py` → `config/urls.py` with `include()` for all three app URL modules
- [x] 7.7 Move `tournament_platform/asgi.py` → `config/asgi.py` (update settings reference)
- [x] 7.8 Move `tournament_platform/wsgi.py` → `config/wsgi.py` (update settings reference)

## 8. Write Per-App Migrations

- [x] 8.1 Create `app/apps/users/migrations/0001_initial.py` (`app_label = 'users'`; `User` table) + `0002_elo_history.py` for `EloHistory` (after tournaments)
- [x] 8.2 Create `app/apps/teams/migrations/0001_initial.py` (`app_label = 'teams'`; `dependencies = [('users', '0001_initial')]`; `Team`, `TeamMember` tables)
- [x] 8.3 Create `app/apps/tournaments/migrations/0001_initial.py` (`app_label = 'tournaments'`; `dependencies = [('users', '0001_initial'), ('teams', '0001_initial')]`; `Tournament`, `TournamentTeam`, `Match` tables)
- [x] 8.4 Delete `core/migrations/0001_initial.py` and the `core` migrations package

## 9. Update manage.py and Config Files

- [x] 9.1 Update `manage.py` default `DJANGO_SETTINGS_MODULE` to `config.settings.development`
- [x] 9.2 Update `pytest.ini` `DJANGO_SETTINGS_MODULE` to `config.settings.testing`
- [x] 9.3 Update `mutmut_config.py` `paths_to_mutate` to `app/apps/` and `app/common/`
- [x] 9.4 Review `setup.cfg` for any paths referencing `core` or `tournament_platform` and update

## 10. Reorganise Tests

- [x] 10.1 Create `tests/users/__init__.py`, `tests/teams/__init__.py`, `tests/tournaments/__init__.py`
- [x] 10.2 Move `tests/core/test_models_user.py` → `tests/users/test_models.py` (update imports)
- [x] 10.3 Move `tests/core/test_models_team.py` → `tests/teams/test_models.py` (update imports)
- [x] 10.4 Merge `tests/core/test_models_match.py` + `test_models_tournament.py` → `tests/tournaments/test_models.py` (update imports)
- [x] 10.5 Split `tests/core/test_views.py` into `tests/users/test_views.py`, `tests/teams/test_views.py`, `tests/tournaments/test_views.py` (update imports)
- [x] 10.6 Move `tests/test_sql_queries.py` → `tests/tournaments/test_sql_queries.py` (update imports)
- [x] 10.7 Verify `tests/conftest.py` fixtures resolve for all new test sub-packages

## 11. Verify and Clean Up

- [x] 11.1 Run `grep -r "from core\|import core\|from tournament_platform\|import tournament_platform" app/ tests/` — expect zero matches
- [x] 11.2 Run `python manage.py check --settings=config.settings.development` — expect zero errors
- [x] 11.3 Run `python manage.py check --settings=config.settings.testing` — expect zero errors
- [x] 11.4 Run `pytest` from `django-api/` — expect all previously passing tests to pass with same count
- [x] 11.5 Delete the old `app/core/` directory and `app/tournament_platform/` directory after confirming all content is moved
