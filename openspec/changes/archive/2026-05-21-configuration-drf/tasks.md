## 1. Dependencies & Settings

- [x] 1.1 Verify `django-filter` is in `requirements/base.txt`; add it if absent
- [x] 1.2 Add `django_filters` to `INSTALLED_APPS` in `config/settings/base.py`
- [x] 1.3 Set `DEFAULT_PAGINATION_CLASS`, `PAGE_SIZE`, `DEFAULT_FILTER_BACKENDS`, `DEFAULT_THROTTLE_CLASSES`, `DEFAULT_THROTTLE_RATES`, and `EXCEPTION_HANDLER` in the `REST_FRAMEWORK` dict in `config/settings/base.py`

## 2. Custom Exception Handler (Throttling)

- [x] 2.1 Create `core/exceptions.py` with `custom_exception_handler` that intercepts `Throttled`, builds the structured JSON body (`error`, `message`, `retry_after_seconds = math.ceil(exc.wait)`), and delegates all other exceptions to DRF's default handler
- [x] 2.2 Write failing test: anonymous client exceeds 100 req/h → 429 with correct JSON body
- [x] 2.3 Write failing test: `retry_after_seconds` is ceiling integer (e.g., 127.4 s → 128)
- [x] 2.4 Write failing test: non-throttle exception still returns standard DRF shape
- [x] 2.5 Run tests; confirm all three fail, then implement until green

## 3. Pagination — Matches CursorPagination

- [x] 3.1 Create `core/pagination.py` with `MatchCursorPagination(CursorPagination)` setting `page_size = 20` and `ordering = "-played_at"`
- [x] 3.2 Set `pagination_class = MatchCursorPagination` on `MatchViewSet`
- [x] 3.3 Write failing test: `GET /api/matches/` response has `next`/`previous` but no `count` key
- [x] 3.4 Write failing test: cursor stays consistent when a new match is inserted between two page fetches
- [x] 3.5 Run tests; confirm fail, implement until green

## 4. Filtering — Tournament Status

- [x] 4.1 `TournamentFilterSet` in `core/views.py` using `ChoiceFilter` for `status` (pre-existing, uses `Tournament.STATUS_CHOICES`); invalid value raises ValidationError → 400
- [x] 4.2 `filterset_class = TournamentFilterSet` on `TournamentViewSet` (pre-existing)
- [x] 4.3 Test: `GET /api/tournaments/?status=invalid` → 400 (pre-existing test)
- [x] 4.4 Test: `GET /api/tournaments/?status=open` → 200, all results have `status="open"` (pre-existing test)
- [x] 4.5 All tournament filter tests green

## 5. Filtering — Match Status & Tournament ID

- [x] 5.1 `MatchFilterSet` in `core/views.py` extended with `ChoiceFilter` for `status` (`scheduled`, `ongoing`, `finished`) alongside existing `tournament_id` NumberFilter
- [x] 5.2 `filterset_class = MatchFilterSet` on `MatchViewSet` (pre-existing)
- [x] 5.3 Write failing test: `GET /api/matches/?status=postponed` → 400
- [x] 5.4 Write failing test: `GET /api/matches/?status=ongoing` → 200, all results have `status="ongoing"`
- [x] 5.5 Write failing test: `GET /api/matches/?tournament_id=9999` (non-existent) → 200 empty list
- [x] 5.6 Run tests; confirm fail, implement until green

## 6. Filtering — Teams Tournament ID

- [x] 6.1 Create `TeamFilterSet` in `core/views.py` with `NumberFilter` for `tournament_id` (via `tournamentteam__tournament_id`)
- [x] 6.2 Set `filterset_class = TeamFilterSet` on `TeamViewSet`
- [x] 6.3 Write failing test: `GET /api/teams/?tournament_id=2` returns only teams in tournament 2
- [x] 6.4 Write failing test: `GET /api/teams/?tournament_id=9999` → 200 empty list
- [x] 6.5 Run tests; confirm fail, implement until green

## 7. Filtering — Users Role (Admin Only)

- [x] 7.1 Create `UserFilterSet` in `core/views.py` with `ChoiceFilter` for `role`; viewset overrides `filter_queryset` to raise `PermissionDenied` for non-admins
- [x] 7.2 Set `filterset_class = UserFilterSet` on `UserViewSet`
- [x] 7.3 Write failing test: admin `GET /api/users/?role=player` → 200, all results have `role="player"`
- [x] 7.4 Write failing test: non-admin `GET /api/users/?role=player` → 403
- [x] 7.5 Write failing test: admin `GET /api/users/?role=superuser` (invalid) → 400
- [x] 7.6 Run tests; confirm fail, implement until green

## 8. Filtering — Rankings Tournament ID

- [x] 8.1 Rankings endpoint does not exist yet — skipped (out of scope for this change)
- [x] 8.2 Rankings endpoint does not exist yet — skipped
- [x] 8.3 Rankings endpoint does not exist yet — skipped
- [x] 8.4 Rankings endpoint does not exist yet — skipped

## 9. Serializer Split — core app (all models live in single `core` app)

- [x] 9.1 Write failing test: importing `from core.serializers import UserCreateSerializer` raises `ModuleNotFoundError`
- [x] 9.2 Create `core/input.py` with `UserCreateSerializer`, `TeamCreateSerializer`, `TournamentCreateSerializer`, `MatchReportSerializer`
- [x] 9.3 Create `core/output.py` with `UserResponseSerializer`, `UserListSerializer`, `TeamResponseSerializer`, `TeamListSerializer`, `TournamentResponseSerializer`, `TournamentListSerializer`, `MatchResponseSerializer`, `MatchListSerializer`, `TeamMemberSerializer`, `TournamentTeamSerializer`
- [x] 9.4 Update all imports in `core/views.py` to reference `core.input` and `core.output`
- [x] 9.5 Update `tests/core/test_serializers.py` imports to `core.input` / `core.output`
- [x] 9.6 Delete `core/serializers.py`
- [x] 9.7 Run tests; confirm all 176 pass

## 10–13. Serializer Split — separate app tasks

- [x] 10–13 N/A: project uses a single `core` app; all serializer split work was done in task group 9

## 14. Full Regression

- [x] 14.1 Run the complete test suite: 176 passed, 4 subtests passed
- [x] 14.2 Confirm no `serializers.py` exists in `core/` — confirmed deleted
- [x] 14.3 Verified `GET /api/matches/` cursor response has `next`/`previous`, no `count` key (test passes)
- [x] 14.4 Verified `GET /api/tournaments/?status=cancelled` returns 400 (test passes)
