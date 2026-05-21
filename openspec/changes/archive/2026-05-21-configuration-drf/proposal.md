## Why

The API layer lacks a consistent, project-wide DRF configuration: each viewset makes its own
pagination, filtering, and throttle decisions, and serializers mix input validation with output
representation in a single file. This creates inconsistent client behaviour, makes rate limiting
unenforceable, and complicates maintenance as the number of endpoints grows.

## What Changes

- Add global `PageNumberPagination` (PAGE_SIZE = 20) to `REST_FRAMEWORK` settings; override
  with `CursorPagination` on `MatchViewSet` only.
- Register `django-filter` as the global `DEFAULT_FILTER_BACKENDS` and declare per-endpoint
  `filterset_fields` with strict allowed-value validation (invalid values → HTTP 400).
- Add `AnonRateThrottle` (100 req/h) and `UserRateThrottle` (1 000 req/h) with a custom
  exception handler that returns a structured JSON 429 body.
- Split serializers into `input.py` (write) and `output.py` (read) in every app that has write
  endpoints; `rankings` gets `output.py` only.
- Remove any `serializers.py` files in the affected apps after the split is complete.

## Capabilities

### New Capabilities

- `drf-pagination`: Global PageNumberPagination (PAGE_SIZE=20) with CursorPagination override for matches
- `drf-filtering`: Per-endpoint django-filter integration with strict status validation returning HTTP 400
- `drf-throttling`: AnonRateThrottle / UserRateThrottle with custom structured 429 response body
- `drf-serializer-split`: input.py / output.py separation across users, teams, tournaments, matches, rankings

### Modified Capabilities

- `match-api`: Pagination class changed from PageNumber to Cursor; filter fields added (`tournament_id`, `status`)
- `tournament-api`: Filter field added (`status` with strict validation)
- `team-api`: Filter field added (`tournament_id`)
- `user-list-api`: Filter field added (`role`, admin-only endpoint)
- `match-tracking`: Serializers split from single file into input.py / output.py

## Impact

- **Settings**: `config/settings/base.py` — `REST_FRAMEWORK` dict extended
- **Apps affected**: `users`, `teams`, `tournaments`, `matches`, `rankings`
- **New files**: `input.py`, `output.py` in each affected app; custom exception handler module
- **Removed files**: `serializers.py` in each affected app (after split)
- **Dependencies**: `django-filter` added to `requirements/base.txt` if not already present
- **Clients**: No breaking changes to response shapes; pagination envelope format is unchanged
