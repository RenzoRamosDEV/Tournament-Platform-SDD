## 1. Project & App Setup

- [x] 1.1 Install Django, Django REST Framework, and psycopg2 (add to requirements file)
- [x] 1.2 Create Django project (`tournament_platform`) and `core` app
- [x] 1.3 Set `AUTH_USER_MODEL = 'core.User'` in settings before any migration
- [x] 1.4 Configure PostgreSQL database connection in settings

## 2. User Model & Manager

- [x] 2.1 Write failing tests for `User` model: default ELO, unique username, role CHECK, deletion guard
- [x] 2.2 Implement `UserManager` with `create_user` and `create_superuser`
- [x] 2.3 Implement `User` model extending `AbstractBaseUser` + `PermissionsMixin` with all fields, `CheckConstraint` for role, and DESC index on `elo`

## 3. Team Models

- [x] 3.1 Write failing tests for `Team`: unique name, owner FK RESTRICT, auto-member not created
- [x] 3.2 Write failing tests for `TeamMember`: composite PK uniqueness, joined_at default, RESTRICT on delete
- [x] 3.3 Implement `Team` model with `owner` FK ON DELETE RESTRICT
- [x] 3.4 Implement `TeamMember` model with `UniqueConstraint` on (`user_id`, `team_id`) and `joined_at` default

## 4. Tournament Models

- [x] 4.1 Write failing tests for `Tournament`: status default, status/format CHECK, end_date >= start_date CHECK, max_teams > 0 CHECK
- [x] 4.2 Write failing tests for `TournamentTeam`: composite PK uniqueness, registered_at default
- [x] 4.3 Implement `Tournament` model with all `CheckConstraint`s
- [x] 4.4 Implement `TournamentTeam` model with `UniqueConstraint` on (`tournament_id`, `team_id`)

## 5. Match Model

- [x] 5.1 Write failing tests for `Match`: score defaults, status CHECK, winner_team_id validation constraint, NULL winner allowed, invalid winner rejected
- [x] 5.2 Implement `Match` model with all FKs, `CheckConstraint` for winner, indexes on `tournament_id` and `played_at`

## 6. Migrations

- [x] 6.1 Run `python manage.py makemigrations core` and verify `0001_initial.py` is generated
- [ ] 6.2 Run `python manage.py migrate` against a local PostgreSQL instance and confirm all tables, constraints, and indexes are created

## 7. DRF Serializers

- [x] 7.1 Write failing tests for each serializer: field presence, read-only fields, nested representation
- [x] 7.2 Implement `UserSerializer` (exclude `password` from read responses)
- [x] 7.3 Implement `TeamSerializer` and `TeamMemberSerializer`
- [x] 7.4 Implement `TournamentSerializer` and `TournamentTeamSerializer`
- [x] 7.5 Implement `MatchSerializer` with `validate()` for winner constraint (friendly error before DB)

## 8. DRF ViewSets & Router

- [x] 8.1 Write failing tests for router registration: all six endpoints return HTTP 200/405 on list/detail
- [x] 8.2 Implement `ModelViewSet` for all six models in `views.py`
- [x] 8.3 Register all ViewSets with `DefaultRouter` in `urls.py` and wire into project URLs

## 9. Mutation Testing & Coverage

- [x] 9.1 Run mutation testing (e.g., `mutmut`) targeting models and serializers; achieve > 95% mutation score
- [x] 9.2 Document any surviving mutants with justification
