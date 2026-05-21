# Requirements: Django REST Framework Global Configuration

## Purpose
Establish a consistent, project-wide DRF configuration that enforces pagination, filtering,
rate limiting, and a clear serializer responsibility boundary across all API apps. This removes
ad-hoc per-view decisions and ensures uniform API behaviour for clients.

## Scope
- **In scope:**
  - Global `REST_FRAMEWORK` settings in `config/settings/base.py`
  - `PageNumberPagination` (default) and `CursorPagination` (matches only)
  - `django-filter` integration with per-endpoint filter fields and valid value sets
  - Throttle classes for anonymous and authenticated users with a custom 429 body
  - Serializer file split (`input.py` / `output.py`) for all write-capable apps
  - `output.py`-only module for the `rankings` app (read-only)
- **Out of scope:**
  - Business logic inside serializers (validation rules belong in model/service layer)
  - Authentication backends or permission classes
  - Any endpoint not listed in the filter table below
  - Frontend implementation of pagination or error handling

---

## Requirements

### Pagination

1. The default pagination class for all endpoints is `PageNumberPagination` with `PAGE_SIZE = 20`,
   configured globally in `REST_FRAMEWORK`.

2. `GET /api/matches/` MUST use `CursorPagination` instead of `PageNumberPagination`.
   This is set at the viewset level (`MatchViewSet.pagination_class = CursorPagination`) to
   prevent page-number desynchronisation when match records are created or updated during a
   live tournament.

3. All other endpoints (`/tournaments/`, `/teams/`, `/users/`, `/rankings/`) use the global
   `PageNumberPagination` and MUST NOT declare a local `pagination_class`.

### Filtering

4. `django-filter` is installed and registered as the global `DEFAULT_FILTER_BACKENDS` in
   `REST_FRAMEWORK`.

5. Each endpoint exposes exactly the filter fields listed below — no more, no less:

   | Endpoint | Filter field | Allowed values |
   |---|---|---|
   | `GET /api/tournaments/` | `status` | `draft`, `open`, `in_progress`, `closed` |
   | `GET /api/matches/` | `tournament_id` | Any existing Tournament PK |
   | `GET /api/matches/` | `status` | `scheduled`, `ongoing`, `finished` |
   | `GET /api/teams/` | `tournament_id` | Any existing Tournament PK |
   | `GET /api/users/` | `role` | Admin-only endpoint; allowed values defined by the User model |
   | `GET /api/rankings/` | `tournament_id` | Any existing Tournament PK |

6. A request supplying a `?status=` value not in the allowed set for that model MUST return
   `HTTP 400 Bad Request` with a descriptive error message. It MUST NOT return `HTTP 200`
   with an empty list.

7. Endpoints not listed in requirement 5 do not expose any filter parameters.

### Throttling

8. The global throttle classes are `AnonRateThrottle` and `UserRateThrottle`, configured in
   `REST_FRAMEWORK`:
   - Anonymous users: **100 requests per hour**
   - Authenticated users: **1 000 requests per hour**

9. When a client exceeds its rate limit the API MUST return `HTTP 429 Too Many Requests` with
   the standard DRF `Retry-After` header **and** the following JSON body (no other shape is
   acceptable):

   ```json
   {
     "error": "rate_limit_exceeded",
     "message": "Has superado el límite de solicitudes. Intenta de nuevo más tarde.",
     "retry_after_seconds": <integer seconds until reset>
   }
   ```

10. The custom 429 body is produced by a project-level `CustomThrottle` mixin or a custom
    `EXCEPTION_HANDLER` — whichever approach is chosen must not duplicate throttle logic.

### Serializer Separation

11. Every app that accepts write operations MUST contain exactly two serializer files:
    - `input.py` — serializers that validate and deserialise incoming request data
    - `output.py` — serializers that serialise outgoing response data

12. The `rankings` app is read-only and MUST contain only `output.py`. It MUST NOT have
    an `input.py` file.

13. The serializer split applies to these apps and classes:

    | App | `input.py` | `output.py` |
    |---|---|---|
    | `users` | `UserCreateSerializer` | `UserResponseSerializer`, `UserListSerializer` |
    | `teams` | `TeamCreateSerializer` | `TeamResponseSerializer`, `TeamListSerializer` |
    | `tournaments` | `TournamentCreateSerializer` | `TournamentResponseSerializer`, `TournamentListSerializer` |
    | `matches` | `MatchReportSerializer` | `MatchResponseSerializer`, `MatchListSerializer` |
    | `rankings` | *(none)* | `RankingResponseSerializer` |

14. `ListSerializer` variants expose only summary fields (`id`, `name`, `status`).
    `ResponseSerializer` variants expose the full object including nested relations.

15. No serializer file named `serializers.py` may exist in any of the apps listed above after
    this configuration is applied.

---

## Scenarios

### Invalid Status Filter Returns 400
- GIVEN a client sends `GET /api/tournaments/?status=cancelled`
- WHEN the view processes the request
- THEN the API returns `HTTP 400 Bad Request` with a body identifying `status` as the invalid field and listing the accepted values (`draft`, `open`, `in_progress`, `closed`)

### Anonymous User Hits Rate Limit
- GIVEN an unauthenticated client has sent 100 requests within the current hour
- WHEN the client sends request number 101
- THEN the API returns `HTTP 429` with a `Retry-After` header and a JSON body matching the exact shape in requirement 9

### Authenticated User Stays Within Limit
- GIVEN an authenticated user has sent 1 000 requests within the current hour
- WHEN the client sends request number 1 000
- THEN the API returns `HTTP 200` (the limit is inclusive)

### Matches Pagination Stays Consistent Under Live Updates
- GIVEN `GET /api/matches/?tournament_id=5` is paginated with `CursorPagination`
- WHEN new match records are inserted between two page requests
- THEN the second page cursor returns the next set of records without skipping or duplicating any match

### Matches Endpoint Rejects Unknown Status
- GIVEN a client sends `GET /api/matches/?status=postponed`
- WHEN the view processes the request
- THEN the API returns `HTTP 400 Bad Request`; `postponed` is not in `{scheduled, ongoing, finished}`

### List vs Response Serializer Detail Level
- GIVEN a client requests `GET /api/teams/` (list)
- WHEN the response is serialised with `TeamListSerializer`
- THEN each item contains only `id`, `name`, and `status` — no nested relations
- GIVEN a client requests `GET /api/teams/{id}/` (detail)
- WHEN the response is serialised with `TeamResponseSerializer`
- THEN the item contains the full object including nested relations
