# Requirements: Django Project Bootstrap for Tournament Platform API

## Purpose
Stand up the Django project skeleton that will serve as the Python microservice in a multi-service
architecture. The goal is to configure the project once, correctly, so that later feature work
starts from a solid, environment-agnostic foundation with the correct database schema, auth
strategy, and developer tooling in place.

## Scope
- **In scope:**
  - `django-admin startproject tournament_api` and `python manage.py startapp core`
  - `settings.py` configured for PostgreSQL, CORS, DRF, and environment-based secrets
  - Custom `AbstractBaseUser` model with all required fields
  - All eight models from the agreed schema with correct relationships and constraints
  - Initial migration set
  - `python manage.py seed_data` management command
- **Out of scope:**
  - DRF views, serializers, or URL routes (future work)
  - The Java authentication service implementation
  - Docker / deployment configuration
  - Frontend or client code

---

## Requirements

### Project Structure
1. The project is created with `django-admin startproject tournament_api` at the repository root.
2. A single Django app named `core` is created with `python manage.py startapp core` and registered in `INSTALLED_APPS`.

### Environment & Secrets
3. All environment-specific values are read from a `.env` file using `python-decouple`. No secrets or environment-specific strings are hardcoded in `settings.py`.
4. The following variables must be read from the environment:

   | Variable | Type | Dev default | Notes |
   |---|---|---|---|
   | `SECRET_KEY` | `str` | — | No default; raises error if missing |
   | `DEBUG` | `bool` | `True` | |
   | `DB_NAME` | `str` | — | |
   | `DB_USER` | `str` | — | |
   | `DB_PASSWORD` | `str` | — | |
   | `DB_HOST` | `str` | `localhost` | |
   | `DB_PORT` | `int` | `5432` | |
   | `CORS_ALLOWED_ORIGINS` | `str` | `http://localhost:3000,http://localhost:5073` | Parsed as comma-separated list |
   | `PAGE_SIZE` | `int` | `20` | DRF default page size |

### Database
5. The database backend is `django.db.backends.postgresql` using `psycopg2`. Connection parameters are sourced entirely from environment variables (Requirement 4).

### CORS
6. `django-cors-headers` is installed and `corsheaders.middleware.CorsMiddleware` is placed as the **first** middleware in `MIDDLEWARE`.
7. `CORS_ALLOWED_ORIGINS` is populated by splitting the `CORS_ALLOWED_ORIGINS` env var on commas and stripping whitespace from each entry.

### Django REST Framework
8. DRF is installed (`rest_framework` in `INSTALLED_APPS`) with the following `REST_FRAMEWORK` settings:
   - `DEFAULT_AUTHENTICATION_CLASSES`: a single custom class `core.authentication.JavaJWTAuthentication` (to be implemented in a later task).
   - `DEFAULT_PERMISSION_CLASSES`: `['rest_framework.permissions.IsAuthenticated']`
   - `DEFAULT_PAGINATION_CLASS`: `rest_framework.pagination.PageNumberPagination`
   - `PAGE_SIZE`: read from the `PAGE_SIZE` env var (default `20`).

### User Model
9. A custom user model `core.models.User` extends `AbstractBaseUser` and `PermissionsMixin`. Django's `AUTH_USER_MODEL` is set to `'core.User'`.
10. The `User` model has exactly these fields:

    | Field | Type | Constraints |
    |---|---|---|
    | `id` | `AutoField` (PK) | — |
    | `username` | `CharField(max_length=150)` | `unique=True` |
    | `email` | `EmailField` | `unique=True` |
    | `password` | managed by `AbstractBaseUser` | `password_hash` is the underlying column |
    | `role` | `CharField(max_length=20)` | choices: `admin`, `organizer`, `player`; default `player`; enforced at application level via Django choices |
    | `elo` | `IntegerField` | default `1000` |
    | `avatar_url` | `URLField` | `blank=True, null=True` |
    | `created_at` | `DateTimeField` | `auto_now_add=True` |

11. `USERNAME_FIELD = 'email'`. `REQUIRED_FIELDS = ['username']`.
12. A custom `UserManager` extends `BaseUserManager` and provides `create_user` and `create_superuser` methods.

### Additional Models
13. All models below live in `core/models.py` and use explicit `db_table` names matching the schema names.

    **Team**
    - `id` (PK), `name CharField(max_length=100, unique=True)`, `owner FK(User, on_delete=PROTECT)`, `created_at auto_now_add`

    **TeamMember** (bridge table)
    - `team FK(Team, on_delete=CASCADE)`, `user FK(User, on_delete=CASCADE)`
    - `joined_at auto_now_add`
    - `Meta.unique_together = [('team', 'user')]`

    **Tournament**
    - `id` (PK), `name CharField(max_length=200)`, `status CharField` choices: `draft/open/ongoing/finished`, default `draft`
    - `format CharField` choices: `single_elimination/round_robin`
    - `max_teams PositiveIntegerField`, `start_date DateField`, `end_date DateField`
    - `created_by FK(User, on_delete=PROTECT)`

    **TournamentTeam** (inscription table)
    - `tournament FK(Tournament, on_delete=CASCADE)`, `team FK(Team, on_delete=CASCADE)`
    - `registered_at auto_now_add`
    - `Meta.unique_together = [('tournament', 'team')]`

    **Match**
    - `id` (PK), `tournament FK(Tournament, on_delete=CASCADE)`
    - `team_a FK(Team, on_delete=PROTECT, related_name='matches_as_a')`
    - `team_b FK(Team, on_delete=PROTECT, related_name='matches_as_b')`
    - `winner_team FK(Team, null=True, blank=True, on_delete=PROTECT, related_name='won_matches')` — `NULL` means match not finished
    - `score_a IntegerField(default=0)`, `score_b IntegerField(default=0)`
    - `status CharField` choices: `scheduled/ongoing/finished`, default `scheduled`
    - `played_at DateTimeField(null=True, blank=True)`

    **EloHistory**
    - `id` (PK), `user FK(User, on_delete=CASCADE)`, `match FK(Match, on_delete=CASCADE)`
    - `elo_before IntegerField`, `elo_after IntegerField`, `changed_at auto_now_add`

14. No draws are possible. `winner_team` must be either `team_a` or `team_b` when the match `status` is `finished`. This invariant is enforced in the model's `clean()` method, not at the database level.

### Migrations
15. A single initial migration is generated with `python manage.py makemigrations` and applies cleanly with `python manage.py migrate` against an empty PostgreSQL database.

### Seed Data Management Command
16. The command is invoked as `python manage.py seed_data`.
17. It creates the following entities using `get_or_create` (keyed on `username`/`name` as appropriate), making it safe to run multiple times without duplicating data:
    - **20 users**: 1 with `role=admin`, 3 with `role=organizer`, 16 with `role=player`. All start with `elo=1000`.
    - **6 teams** owned by organizer users.
    - **3 tournaments**: one with `status=finished`, one `status=ongoing`, one `status=open`.
    - **~12 matches** distributed across the three tournaments, with `EloHistory` rows for each finished match.
18. The command accepts an optional `--clear` flag. When `--clear` is passed:
    - It checks `settings.DEBUG`. If `DEBUG=False`, the command exits immediately with error message: `"--clear is not allowed outside DEBUG mode."` No data is deleted.
    - If `DEBUG=True`, all rows in all `core` tables are deleted before re-seeding.

---

## Scenarios

### Seed Data — Idempotent Run
- GIVEN the database already contains the seeded users, teams, and tournaments
- WHEN `python manage.py seed_data` is run a second time
- THEN no duplicate rows are created and the command exits with return code 0

### Seed Data — Clear Flag in Production Guard
- GIVEN `DEBUG=False` in the environment
- WHEN `python manage.py seed_data --clear` is run
- THEN the command prints `"--clear is not allowed outside DEBUG mode."` and exits with a non-zero return code, leaving all existing data untouched

### Seed Data — Clear Flag in Development
- GIVEN `DEBUG=True` and existing data in the database
- WHEN `python manage.py seed_data --clear` is run
- THEN all existing `core` model data is deleted and 20 users, 6 teams, 3 tournaments, and ~12 matches with EloHistory are created from scratch

### CORS — Allowed Origin from Environment
- GIVEN `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5073` in `.env`
- WHEN a browser sends an `OPTIONS` preflight from `http://localhost:3000`
- THEN the response includes `Access-Control-Allow-Origin: http://localhost:3000`

### CORS — Unlisted Origin Rejected
- GIVEN `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5073` in `.env`
- WHEN a browser sends an `OPTIONS` preflight from `http://evil.example.com`
- THEN the response does NOT include `Access-Control-Allow-Origin`

### User ELO Default
- GIVEN a new `User` object is created without specifying `elo`
- WHEN the object is saved to the database
- THEN `user.elo` equals `1000`

### Role Constraint — Invalid Value
- GIVEN a `User` instance with `role='referee'` (not a valid choice)
- WHEN `full_clean()` is called
- THEN a `ValidationError` is raised

### Match Finished Without Winner
- GIVEN a `Match` instance with `status='finished'` and `winner_team=None`
- WHEN `full_clean()` is called
- THEN a `ValidationError` is raised

### Match Winner Not a Participant
- GIVEN a `Match` with `team_a=TeamA`, `team_b=TeamB`, `status='finished'`, and `winner_team=TeamC` (a third team)
- WHEN `full_clean()` is called
- THEN a `ValidationError` is raised
