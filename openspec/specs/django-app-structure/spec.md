## ADDED Requirements

### Requirement: Domain apps replace monolithic core app
The system SHALL organise domain logic into three separate Django apps — `apps.users`, `apps.teams`, and `apps.tournaments` — each containing its own models, serializers, views, URLs, admin, and migrations. No Python module under `app/apps/` or `app/common/` SHALL import from `core` or `tournament_platform`.

#### Scenario: No stale core imports remain
- **WHEN** a grep for `from core`, `import core`, `from tournament_platform`, or `import tournament_platform` is run across `app/` and `tests/`
- **THEN** zero matches are returned

#### Scenario: Django startup check passes
- **WHEN** `python manage.py check --settings=config.settings.development` is executed
- **THEN** the command exits with code 0 and reports no errors

### Requirement: Settings split into environment-specific modules
The system SHALL provide four settings modules: `config.settings.base` (shared), `config.settings.development`, `config.settings.testing`, and `config.settings.production`. Each non-base module SHALL start with `from .base import *` and only declare environment-specific overrides. No setting SHALL be duplicated across modules.

#### Scenario: Testing settings include test-specific overrides
- **WHEN** `config.settings.testing` is imported
- **THEN** it contains all overrides from the original `test_settings.py` (e.g. test database name, fast password hashers, disabled throttling)

#### Scenario: manage.py defaults to development settings
- **WHEN** `manage.py` is executed without setting `DJANGO_SETTINGS_MODULE`
- **THEN** it uses `config.settings.development`

#### Scenario: pytest uses testing settings
- **WHEN** `pytest` is run from `django-api/`
- **THEN** `DJANGO_SETTINGS_MODULE` resolves to `config.settings.testing` via `pytest.ini`

### Requirement: Migrations split into three per-app initial migrations
The system SHALL have exactly three per-app initial migrations. `apps/users/migrations/0001_initial.py` SHALL have `app_label = 'users'` and create the `User` and `EloHistory` tables. `apps/teams/migrations/0001_initial.py` SHALL have `app_label = 'teams'`, declare `dependencies = [('users', '0001_initial')]`, and create the `Team` and `TeamMember` tables. `apps/tournaments/migrations/0001_initial.py` SHALL have `app_label = 'tournaments'`, declare `dependencies = [('users', '0001_initial'), ('teams', '0001_initial')]`, and create the `Tournament`, `TournamentTeam`, and `Match` tables. No migration SHALL reference the `core` app label.

#### Scenario: Clean database migration produces correct schema
- **WHEN** `python manage.py migrate` is run on a blank database
- **THEN** all tables are created, no `django_migrations` row references `core`, and `python manage.py check` reports no errors

#### Scenario: FK relations resolve at startup
- **WHEN** Django starts with the three-app configuration
- **THEN** `python manage.py check` reports no `fields.E300` or `fields.E301` errors

### Requirement: Shared utilities live in common package
The system SHALL provide `app/common/exceptions.py`, `app/common/pagination.py`, and `app/common/permissions.py`. `exceptions.py` and `pagination.py` SHALL contain exactly the code currently in `core/exceptions.py` and `core/pagination.py` with updated import paths. `permissions.py` SHALL contain any permission classes from `core/` or be an empty module if none exist.

#### Scenario: common modules importable
- **WHEN** `from common.exceptions import ...`, `from common.pagination import ...`, and `from common.permissions import ...` are used in any app module
- **THEN** the imports resolve without error at Django startup

### Requirement: All URL routes remain reachable under original prefixes
The system SHALL configure `config/urls.py` to include URL patterns for all three apps using `include()`, preserving the exact URL prefixes from the original `tournament_platform/urls.py`.

#### Scenario: All original routes present
- **WHEN** Django's URL resolver is loaded with `config.settings.development`
- **THEN** every route that existed before the migration resolves to the same view with the same HTTP method and URL pattern

### Requirement: Tests reorganised to mirror app structure
The system SHALL relocate test files from `tests/core/` to `tests/users/`, `tests/teams/`, and `tests/tournaments/` as specified in the target tree. `tests/conftest.py` SHALL remain at the root of `tests/` and its fixtures SHALL be discoverable by all three test sub-packages.

#### Scenario: All tests collected and passing
- **WHEN** `pytest django-api/tests/` is executed after reorganisation
- **THEN** the number of collected tests equals the number collected before the migration and all previously passing tests still pass

### Requirement: mutmut configuration points to new source paths
The system SHALL update `mutmut_config.py` so that `paths_to_mutate` references `app/apps/` and `app/common/` instead of `app/core/`.

#### Scenario: mutmut config reflects new paths
- **WHEN** `mutmut_config.py` is read
- **THEN** `paths_to_mutate` contains `app/apps/` and `app/common/` and does not contain `app/core/`
