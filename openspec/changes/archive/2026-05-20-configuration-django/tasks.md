## 1. Project Scaffolding & Dependencies

- [x] 1.1 Run `django-admin startproject tournament_api .` at the repository root
- [x] 1.2 Run `python manage.py startapp core` to create the core app
- [x] 1.3 Add `Django`, `djangorestframework`, `psycopg2-binary`, `django-cors-headers`, and `python-decouple` to `requirements.txt`
- [x] 1.4 Create `.env.example` with placeholder values for `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `CORS_ALLOWED_ORIGINS`, `PAGE_SIZE`
- [x] 1.5 Add `.env` to `.gitignore`

## 2. Settings Configuration

- [x] 2.1 Replace default `SECRET_KEY` and `DEBUG` with `python-decouple` reads; raise `UndefinedValueError` if `SECRET_KEY` is absent
- [x] 2.2 Configure `DATABASES['default']` with `django.db.backends.postgresql`; read all five DB params from environment variables with appropriate defaults
- [x] 2.3 Add `corsheaders.middleware.CorsMiddleware` as the first entry in `MIDDLEWARE`; wire `CORS_ALLOWED_ORIGINS` by splitting the env var on commas
- [x] 2.4 Add `rest_framework` and `corsheaders` to `INSTALLED_APPS`; register `core` app
- [x] 2.5 Configure `REST_FRAMEWORK` dict with `JavaJWTAuthentication`, `IsAuthenticated`, `PageNumberPagination`, and `PAGE_SIZE` from env (default 20)
- [x] 2.6 Set `AUTH_USER_MODEL = 'core.User'`

## 3. Custom User Model

- [x] 3.1 Write failing tests for `User` model: ELO default, email as login field, valid/invalid role, `create_user`, `create_superuser`
- [x] 3.2 Implement `UserManager` with `create_user` and `create_superuser` methods
- [x] 3.3 Implement `User` model extending `AbstractBaseUser` and `PermissionsMixin` with all required fields, `USERNAME_FIELD = 'email'`, `REQUIRED_FIELDS = ['username']`
- [x] 3.4 Run tests — all must pass

## 4. Core Models

- [x] 4.1 Write failing tests for `Team`, `TeamMember`, `Tournament`, `TournamentTeam`, `Match`, `EloHistory` — covering constraints, defaults, and CASCADE/PROTECT behavior
- [x] 4.2 Write failing tests for `Match.clean()` — finished without winner, winner not a participant, valid finished match
- [x] 4.3 Implement `Team` and `TeamMember` models with `db_table`, relationships, and `unique_together`
- [x] 4.4 Implement `Tournament` and `TournamentTeam` models with choices, defaults, and `unique_together`
- [x] 4.5 Implement `Match` model with all FK relationships, choices, nullable fields, and `clean()` validation
- [x] 4.6 Implement `EloHistory` model
- [x] 4.7 Run tests — all must pass

## 5. Initial Migration

- [x] 5.1 Run `python manage.py makemigrations` and verify `core/migrations/0001_initial.py` is generated
- [x] 5.2 Run `python manage.py migrate` against a clean PostgreSQL database and verify it completes without error

## 6. Seed Data Command

- [x] 6.1 Write failing tests for `seed_data`: correct entity counts, idempotency (two runs), `--clear` blocked when `DEBUG=False`, `--clear` wipes and re-seeds when `DEBUG=True`, finished matches have EloHistory rows
- [x] 6.2 Create `core/management/commands/seed_data.py` with `add_arguments` wiring the `--clear` flag
- [x] 6.3 Implement `--clear` guard: check `settings.DEBUG`, print error and exit non-zero if False
- [x] 6.4 Implement `--clear` wipe: delete all core model rows in reverse dependency order
- [x] 6.5 Implement entity creation: 20 users (1 admin, 3 organizers, 16 players) via `get_or_create`
- [x] 6.6 Implement 6 teams owned by organizer users via `get_or_create`
- [x] 6.7 Implement 3 tournaments (finished/ongoing/open) via `get_or_create`
- [x] 6.8 Implement ~12 matches with `EloHistory` rows for finished matches
- [x] 6.9 Run tests — all must pass

## 7. JavaJWTAuthentication Stub

- [x] 7.1 Create `core/authentication.py` with a `JavaJWTAuthentication` class extending `BaseAuthentication`; implement `authenticate()` to return `None` (unauthenticated) — full implementation is a separate task
