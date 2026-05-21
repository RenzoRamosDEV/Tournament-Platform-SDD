## Context

The project exposes REST APIs across five apps (`users`, `teams`, `tournaments`, `matches`,
`rankings`). Currently each viewset independently decides its pagination strategy, no
filtering backend is registered globally, no throttle is enforced, and serializers mix input
validation with response formatting in a single `serializers.py` per app.

This change applies uniform cross-cutting DRF settings without altering any business logic
or database schema.

## Goals / Non-Goals

**Goals:**
- Single source of truth for pagination, filtering, and throttle in `REST_FRAMEWORK` settings
- Deterministic cursor-based pagination for `GET /api/matches/` to survive concurrent writes
- HTTP 400 (not 200+empty) for invalid filter values, enforced via a custom FilterSet
- HTTP 429 with a structured JSON body on rate-limit breach
- Clean serializer boundary: `input.py` owns deserialization; `output.py` owns serialization

**Non-Goals:**
- Changing any business logic (ELO, winner validation, role checks)
- Modifying authentication backends or permission classes
- Altering database schema or migration files
- Adding new API endpoints

## Decisions

### D1 — Global settings in `config/settings/base.py`

All four DRF concerns (pagination, filtering, throttling, exception handler) are set once in
`REST_FRAMEWORK`. Per-view overrides are limited to `MatchViewSet.pagination_class` only.
This minimises divergence and makes the defaults discoverable in one place.

Alternatives considered:
- Per-viewset `filter_backends` / `pagination_class`: rejected because it requires every
  new viewset to re-declare the same defaults and is error-prone.

### D2 — CursorPagination on `MatchViewSet` only

`GET /api/matches/` uses cursor-based pagination because match records are inserted and
updated in real time during live tournaments. PageNumber pagination desynchronises when a
new page is fetched after new rows are inserted (page N shifts).

All other endpoints are not write-heavy during list views, so `PageNumberPagination`
(PAGE_SIZE=20) is sufficient and simpler for clients.

### D3 — Custom FilterSet per endpoint for strict status validation

`django-filter` by default returns an empty list for unknown values. The requirement demands
HTTP 400. This is achieved by subclassing `FilterSet` and overriding `filter_queryset` (or
using a `ChoiceFilter`) so that an unrecognised value raises `ValidationError` and is caught
by DRF's exception handler.

Alternatives considered:
- Overriding `get_queryset` in the viewset: rejected because it duplicates validation logic
  and bypasses the filter layer entirely.

### D4 — Custom exception handler for 429 body

DRF's default `Throttled` exception returns a plain `{"detail": "..."}` body. The frontend
contract requires `{"error": "rate_limit_exceeded", "message": "...", "retry_after_seconds": N}`.

A project-level `custom_exception_handler` in `core/exceptions.py` (or equivalent) intercepts
`Throttled`, extracts `wait`, and serialises the agreed JSON. The default DRF handler is
called for all other exceptions.

Alternatives considered:
- Subclassing `AnonRateThrottle` / `UserRateThrottle`: rejected because throttle classes
  produce the exception, not the response body — the exception handler is the correct hook.

### D5 — `input.py` / `output.py` file split, no `serializers.py`

Each write-capable app gets exactly two files. Existing `serializers.py` files are deleted
after the split. `rankings` app gets only `output.py` since it has no write endpoints.

The distinction within `output.py`:
- `ListSerializer` — id, name, status only (for list views)
- `ResponseSerializer` — full object with nested relations (for detail / write-response views)

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `CursorPagination` requires an ordered queryset; missing `ordering` raises an error | Set `ordering = ["-played_at"]` on `MatchViewSet` or in `MatchCursorPagination.ordering` |
| Deleting `serializers.py` breaks any import not yet updated | Grep all imports before deletion; update in the same PR |
| Custom FilterSet 400 changes existing behaviour for `/api/tournaments/?status=invalid` which already returns 400 in the existing spec — but the valid values differ (`ongoing` vs `in_progress`) | Align the FilterSet choices to match the actual `Tournament.status` model field choices; adjust the spec delta accordingly |
| `retry_after_seconds` is a float in DRF (`throttle_duration`); must be cast to `int` (ceiling) | Use `math.ceil(exc.wait)` in the exception handler |

## Migration Plan

1. Add `django-filter` to `requirements/base.txt` (if absent).
2. Update `REST_FRAMEWORK` in `config/settings/base.py` (pagination, filter backends,
   throttle classes, exception handler).
3. Create `core/exceptions.py` with the custom exception handler.
4. Create `FilterSet` subclasses per app and wire them into viewsets via `filterset_class`.
5. Set `MatchViewSet.pagination_class = MatchCursorPagination`.
6. For each app: create `input.py` and `output.py`, migrate serializer classes, update all
   viewset imports, delete `serializers.py`.
7. Run full test suite; verify no import errors.
8. Rollback: revert `REST_FRAMEWORK` dict and restore `serializers.py` from git history.
