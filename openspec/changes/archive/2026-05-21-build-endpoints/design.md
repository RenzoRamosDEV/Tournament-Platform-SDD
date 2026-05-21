## Context

All domain models (`User`, `Team`, `Tournament`, `Match`, etc.) live in a single `core` app under
`django-api/app/core/`. DRF is already configured with `core.authentication.JavaJWTAuthentication`
and a global default of `IsAuthenticated`. `PAGE_SIZE` is read from the environment (default 20).

**Schema discrepancy to resolve**: The requirements spec names tournament statuses as
`draft / open / in_progress / closed`, but the live model uses `draft / open / ongoing / finished`.
The implementation will use the model's actual choices (`ongoing`, `finished`); the API filter
parameter accepts those exact strings.

**Team ownership**: The `Team` model has a mandatory `owner` FK to `User`. When a team is
created via `POST /api/teams/`, `owner` is set to `request.user` automatically — it is not a
user-supplied field.

## Goals / Non-Goals

**Goals:**
- Expose 7 HTTP endpoints that read from / write to the existing `core` models
- Public GET endpoints accessible without credentials
- JWT-protected POST endpoints using the existing `JavaJWTAuthentication`
- Paginated list responses using the project's standard `PageNumberPagination`
- Status filter on tournaments validated via `django-filter`
- Match result reporting with idempotency guard (non-admin cannot overwrite)

**Non-Goals:**
- Creating separate Django apps per domain — all views stay in `core`
- Adding new models or migrations
- Implementing `JavaJWTAuthentication` (already exists)
- User registration, login, or token endpoints

## Decisions

### 1 — Single `core` app, no new apps
All views, serializers, and URL patterns extend the existing `core` app.

*Alternative*: Create `apps/teams/`, `apps/tournaments/` etc.
*Why rejected*: Models are already co-located in `core`. Splitting now adds boilerplate with no
benefit at this scale; the project can split later if the app grows.

### 2 — `AllowAny` override per read view
Because the DRF default is `IsAuthenticated`, every `ListAPIView` / `RetrieveAPIView` explicitly
sets `permission_classes = [AllowAny]`.

*Alternative*: Change global default to `IsAuthenticatedOrReadOnly`.
*Why rejected*: Other future endpoints may need to be write-only or require auth for reads.
Explicit per-view override is safer and more readable.

### 3 — `django-filter` for query param validation
`FilterSet` with explicit `ChoiceFilter` for `?status=` on tournaments and `NumberFilter` for
`?tournament_id=` on matches. Invalid values return `400` automatically via `FilterSet` validation.

*Alternative*: Manual query param parsing in `get_queryset`.
*Why rejected*: `django-filter` provides free validation, DRF schema generation, and cleaner code.

### 4 — Match result reporting via custom action, not a separate model
`POST /api/matches/{id}/report/` is a DRF `@action` on `MatchViewSet` that mutates `Match` fields
(`winner_team`, `score_a`, `score_b`, `status`, `played_at`) in place.

*Alternative*: A separate `MatchResult` model.
*Why rejected*: The existing `Match` model already holds all result fields; a separate model
would duplicate data and require a migration.

### 5 — Admin overwrite guard at the view layer
If `match.status == "finished"` and `request.user.role != "admin"`, return `409 Conflict`.
Admin users bypass this check and proceed to update.

### 6 — Tournament draft visibility via queryset filtering
`TournamentListView.get_queryset()` excludes `status="draft"` unless `request.user` is
authenticated and has role `admin` or `organizer`.

## Risks / Trade-offs

- **Status name mismatch** → The requirements doc uses `in_progress`/`closed`; the model uses
  `ongoing`/`finished`. Misaligned external docs could confuse API consumers.
  *Mitigation*: Document the actual model values in the OpenAPI schema; update any client code.

- **Single-app growth** → Adding all views to `core` increases coupling.
  *Mitigation*: Accept for now; refactor to sub-apps is a clean split later since models stay put.

- **No rate limiting** → Public GET endpoints have no throttle.
  *Mitigation*: Out of scope for this change; add DRF throttle classes in a follow-up.

## Migration Plan

No migrations required — this change is purely additive (views, serializers, URL wiring).

Deployment steps:
1. Install/confirm `django-filter` in `requirements/`.
2. Add `django_filters` to `INSTALLED_APPS`.
3. Deploy; no downtime needed.

Rollback: remove the new URL includes — no data changes to revert.
