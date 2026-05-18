## Context

The tournament platform is a new greenfield Django service. There is currently no database schema, no Django app structure, and no API layer. This design establishes the relational foundation that all future features depend on.

The platform must handle: user accounts with ELO ratings, team composition, tournament lifecycle management, and match result recording with integrity constraints.

## Goals / Non-Goals

**Goals:**
- Define a normalized PostgreSQL schema (6 tables) with all FKs, CHECK constraints, composite PKs, and performance indexes
- Implement Django models that accurately mirror the schema
- Generate initial migrations via `makemigrations`
- Provide a minimal DRF skeleton: serializers and router-registered ViewSets for all six resources
- Enforce data integrity at the database level (not just application level) wherever possible

**Non-Goals:**
- Authentication or authorization endpoints
- ELO recalculation logic
- Tournament bracket generation
- Frontend or deployment configuration

## Decisions

### Decision 1: Single Django app vs. multiple apps

**Choice:** Single `core` app containing all six models.

**Rationale:** The entities are tightly coupled (matches reference teams and tournaments; team_members couples users and teams). Splitting into separate apps at this stage adds cross-app FK complexity with no modularity benefit. A future refactor can extract apps once domain boundaries are proven.

**Alternatives considered:**
- `users` + `teams` + `tournaments` apps: premature — the schema has no clean seam between these at this stage.

---

### Decision 2: `AbstractUser` vs. custom model for `users`

**Choice:** Custom model (`User`) extending `AbstractBaseUser` + `PermissionsMixin`, with `username` and `password` fields mapped to `password_hash` (stored as `db_column='password_hash'`).

**Rationale:** Django's auth system manages password hashing. Storing a raw `password_hash` column via a plain model means bypassing Django's `make_password` / `check_password`, which is a security regression. Using `AbstractBaseUser` gives us the `password` field (stored as a hash automatically) while keeping full control over the schema.

**Alternatives considered:**
- Plain `models.Model` with a `password_hash` CharField: bypasses Django password hashing — rejected for security.
- `AbstractUser`: brings in `first_name`, `last_name`, `email` fields we don't need — adds unnecessary columns.

---

### Decision 3: Enforcing CHECK constraints (`role`, `status`, `format`)

**Choice:** Use Django `CharField` with `choices` + a `CheckConstraint` in `Meta.constraints` for each enum column.

**Rationale:** Django `choices` validates at the form/serializer layer. `CheckConstraint` enforces the rule at the database level, covering raw SQL updates and direct ORM writes that bypass validation. Both layers are needed.

---

### Decision 4: Composite PKs for junction tables

**Choice:** `team_members` and `tournament_teams` use `UniqueConstraint` + explicit composite `primary_key=False` fields, with `Meta.unique_together` or `UniqueConstraint` standing in for a composite PK (Django ORM does not natively support composite PKs without third-party libraries).

**Rationale:** Django's ORM requires a single auto-generated PK per model. We add a `UniqueConstraint` on `(user_id, team_id)` / `(tournament_id, team_id)` to enforce the logical composite PK at the database level, and suppress the auto `id` column by setting `default_auto_field` scoping or using `AutoField` explicitly only where needed.

**Alternative:** `composite-pk` third-party package — added dependency, not worth it for two junction tables.

---

### Decision 5: Winner validation constraint

**Choice:** Add a `CheckConstraint` on `matches`: `winner_team_id IS NULL OR winner_team_id = team_a_id OR winner_team_id = team_b_id`.

**Rationale:** This is a cross-column constraint that cannot be expressed with Django field validators alone. A DB-level `CheckConstraint` is the correct tool and mirrors the requirement exactly.

---

### Decision 6: Indexes

**Choice:** Explicit `Meta.indexes` on:
- `users.elo` DESC
- `matches.tournament_id`
- `matches.played_at`

**Rationale:** Specified by requirements. Django's `Index` with `fields=['-elo']` generates a DESC index in PostgreSQL.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Django ORM doesn't support composite PKs natively — junction tables get an implicit `id` column | Add `UniqueConstraint` to enforce the logical PK; the extra `id` column is harmless overhead |
| `AbstractBaseUser` requires a custom `UserManager` | Implement a minimal `UserManager` with `create_user` / `create_superuser` |
| `CheckConstraint` on `winner_team_id` is not enforced by DRF serializer validation | Add serializer-level `validate()` to surface friendly errors before hitting the DB |
| `end_date >= start_date` cross-column constraint not in this table | Add `CheckConstraint` in `Tournament.Meta` |

## Migration Plan

1. Create Django project and `core` app
2. Configure `AUTH_USER_MODEL = 'core.User'` before any migration is run
3. Run `python manage.py makemigrations core` — generates `0001_initial.py`
4. Run `python manage.py migrate` on a local PostgreSQL instance to verify
5. Rollback: `python manage.py migrate core zero` drops all core tables

## Open Questions

- Should the DRF ViewSets be read-only stubs (`ReadOnlyModelViewSet`) or full CRUD (`ModelViewSet`)? — Defaulting to `ModelViewSet` for skeleton completeness; restrict permissions in a follow-up auth ticket.
- PostgreSQL version requirement? — Assuming PG 13+ for `CHECK` constraint support with `OR` logic.
