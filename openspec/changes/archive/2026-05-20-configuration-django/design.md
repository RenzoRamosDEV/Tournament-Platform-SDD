## Context

The tournament platform is a multi-service system. The Python service (Django) handles game data, team management, tournament logic, and ELO history. Authentication tokens are issued and validated by a separate Java service. Django must accept those tokens without re-issuing them.

This document covers the one-time bootstrap of the Django project: project structure, settings wiring, custom user model, schema models, and seed tooling. No views or serializers are in scope.

## Goals / Non-Goals

**Goals:**
- Reproducible project setup with zero hardcoded secrets
- Correct `AUTH_USER_MODEL` set before the first migration (irreversible after data exists)
- All eight schema models with proper relationships and `clean()` validation
- Environment-agnostic CORS config
- A safe, idempotent seed command for development

**Non-Goals:**
- DRF views, serializers, or URL routing
- JWT token issuance — that is Java's responsibility
- Docker or CI/CD setup
- Any production deployment concern

## Decisions

### D1 — `AbstractBaseUser` over `AbstractUser`
**Chosen**: `AbstractBaseUser` + `PermissionsMixin`  
**Rationale**: `AbstractUser` ships with `first_name`, `last_name`, and `username` as the login field. Our schema uses `email` as the login field and has no name split. Starting from `AbstractBaseUser` avoids unused columns and removes ambiguity about which identifier is canonical.  
**Alternative considered**: `AbstractUser` with `USERNAME_FIELD = 'email'` — rejected because it still creates `first_name`/`last_name` columns and retains the `username` uniqueness index alongside our own, creating confusion.

### D2 — `python-decouple` for environment variables
**Chosen**: `python-decouple` reading from `.env`  
**Rationale**: Supports type coercion (`bool`, `int`), default values, and works identically in local and CI environments without patching `os.environ`. The `CORS_ALLOWED_ORIGINS` list is parsed by splitting on commas — decouple reads it as a raw string and Python splits it.  
**Alternative considered**: `django-environ` — similar capability but slightly more magic; `python-decouple` has a simpler, more explicit API.

### D3 — Custom JWT authenticator as a stub
**Chosen**: `core.authentication.JavaJWTAuthentication` registered in `DEFAULT_AUTHENTICATION_CLASSES`, with the actual HTTP call to the Java service implemented in a later task.  
**Rationale**: DRF requires `DEFAULT_AUTHENTICATION_CLASSES` to be set at project init to avoid defaulting to session auth. Registering a stub now ensures every endpoint is wired to the correct auth path from day one, with no risk of session-based auth accidentally working in development.

### D4 — Role enforcement at application level only
**Chosen**: Django `choices` on `CharField`, validated by `full_clean()`  
**Rationale**: PostgreSQL `ENUM` types are painful to migrate (requires `ALTER TYPE`, no simple `ALTER TABLE`). Django choices give us validation without a migration cost when roles are extended.  
**Trade-off**: Invalid values can bypass validation if `save()` is called directly without `full_clean()`. Acceptable because all writes go through DRF serializers (future work) which call `full_clean()` automatically.

### D5 — Match integrity enforced in `clean()`, not DB constraints
**Chosen**: `Match.clean()` validates that a finished match has a winner that is one of the two participants.  
**Rationale**: A DB-level `CHECK` constraint referencing other columns on the same row is possible in PostgreSQL but not expressible in Django's ORM without a raw migration. Using `clean()` keeps the constraint visible in Python and testable without a running database.

### D6 — `seed_data --clear` guarded by `DEBUG=True`
**Chosen**: Check `settings.DEBUG` before allowing destructive wipe  
**Rationale**: The command may be deployed in a staging environment that has `DEBUG=False`. A hard guard prevents accidental data loss without requiring a separate management command.

## Risks / Trade-offs

- **`AUTH_USER_MODEL` is permanent after first migration** → Mitigation: document prominently; enforce in onboarding that a fresh DB is required before running `migrate` for the first time.
- **`clean()` can be bypassed by calling `save()` directly** → Mitigation: DRF serializers enforce `full_clean()`; raw ORM usage in tests should explicitly call `full_clean()` before `save()`.
- **Java auth service is not available during local development** → Mitigation: `JavaJWTAuthentication` stub should return `None` (unauthenticated) or accept a dev bypass header controlled by `DEBUG=True` — scoped to the auth task, not this one.
- **`get_or_create` in `seed_data` uses `username`/`name` as the lookup key** → If a username changes between seed runs, a duplicate will be created. Acceptable for dev tooling; `--clear` is the escape hatch.

## Migration Plan

1. Ensure a clean, empty PostgreSQL database exists and `DB_*` env vars are set.
2. Run `python manage.py makemigrations` — produces `core/migrations/0001_initial.py`.
3. Run `python manage.py migrate` — creates all tables.
4. Optionally run `python manage.py seed_data` to populate dev data.
5. **Rollback**: drop the database and start over — no partial migration rollback is defined for the initial migration.
