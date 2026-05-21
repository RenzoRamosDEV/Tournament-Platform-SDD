## Why

The tournament platform has a complete domain model (users, teams, tournaments, matches) but no HTTP interface.
This change exposes that domain via a REST API so clients can list resources and submit match results.

## What Changes

- Add `GET /api/users/` — paginated public list of users
- Add `GET /api/teams/` — paginated public list of teams
- Add `POST /api/teams/` — create a team (any authenticated user)
- Add `GET /api/tournaments/` — paginated public list with optional `?status=` filter; draft tournaments hidden from non-staff
- Add `POST /api/tournaments/` — create a tournament (admin only)
- Add `GET /api/matches/` — paginated public list with optional `?tournament_id=` filter
- Add `POST /api/matches/{id}/report/` — submit or overwrite a match result (authenticated; admin can overwrite)
- Wire all endpoints into the Django URL router
- Add JWT authentication class to DRF settings (read endpoints remain public)

## Capabilities

### New Capabilities
- `user-list-api`: Public paginated endpoint listing users (`GET /api/users/`)
- `team-api`: Public list and authenticated create for teams (`GET /api/teams/`, `POST /api/teams/`)
- `tournament-api`: Public paginated list with status filter and admin-only create (`GET /api/tournaments/`, `POST /api/tournaments/`)
- `match-api`: Public paginated list filtered by tournament and authenticated result reporting (`GET /api/matches/`, `POST /api/matches/{id}/report/`)

### Modified Capabilities

## Impact

- **New files**: `apps/*/serializers.py`, `apps/*/views.py`, `apps/*/urls.py` per domain app
- **Modified files**: project `urls.py` to include new routers; `settings.py` to add DRF + JWT config
- **Dependencies**: `djangorestframework`, `djangorestframework-simplejwt`, `django-filter`
- **No breaking changes** — purely additive; no existing endpoints are modified
