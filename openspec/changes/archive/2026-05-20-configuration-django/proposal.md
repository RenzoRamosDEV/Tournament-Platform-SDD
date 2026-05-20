## Why

The tournament platform's Python microservice needs a fully configured Django project before any feature development can begin. Without a correct initial setup — schema, auth strategy, environment handling, and seed tooling — every subsequent task risks being built on a broken or incomplete foundation.

## What Changes

- Bootstrap Django project (`tournament_api`) and `core` app from scratch
- Configure `settings.py` with PostgreSQL via `psycopg2`, `django-cors-headers`, and Django REST Framework — all values sourced from environment variables via `python-decouple`
- Implement a custom `AbstractBaseUser` model (`core.User`) with `email` as the login field, `role` (admin/organizer/player), and `elo` (default 1000)
- Define all eight schema models in `core/models.py`: `User`, `Team`, `TeamMember`, `Tournament`, `TournamentTeam`, `Match`, `EloHistory`
- Generate and apply the initial database migration
- Add `python manage.py seed_data` management command (idempotent; `--clear` flag guarded by `DEBUG=True`)
- **BREAKING**: `AUTH_USER_MODEL` is set to `core.User` — this must be in place before the first migration runs; changing it later requires wiping the database

## Capabilities

### New Capabilities
- `django-project-setup`: Project scaffolding, `settings.py` configuration, installed apps, middleware order, and environment variable wiring
- `custom-user-model`: `AbstractBaseUser` + `PermissionsMixin` implementation with `UserManager`, role choices, and ELO default
- `core-models`: All remaining schema models (Team, TeamMember, Tournament, TournamentTeam, Match, EloHistory) with relationships, constraints, and `clean()` validation
- `seed-data-command`: `seed_data` management command — idempotent via `get_or_create`, `--clear` flag with `DEBUG` guard

### Modified Capabilities
- `env-config`: Extends the existing env-config spec to include `CORS_ALLOWED_ORIGINS` and `PAGE_SIZE` variables

## Impact

- **New dependencies**: `Django`, `djangorestframework`, `psycopg2-binary`, `django-cors-headers`, `python-decouple`, `djangorestframework-simplejwt` (JWT stub only — token validation delegated to Java service)
- **Database**: Requires an empty PostgreSQL database before `migrate` is run; schema is created entirely by the initial migration
- **Auth**: All DRF endpoints default to `IsAuthenticated`; token validation is wired to a placeholder `core.authentication.JavaJWTAuthentication` class
- **No existing code is modified** — this is a greenfield project setup
