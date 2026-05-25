## ADDED Requirements

### Requirement: Business logic confined to service layer
All business logic — match result reporting, ELO score calculation, and tournament state transitions — SHALL reside exclusively in `services.py` (or a `services/` package) within each Django app. Views MUST NOT contain any business logic. Serializers MUST NOT contain any business logic. Views MUST only call service methods and delegate HTTP response formatting.

#### Scenario: Match result reported via service
- **WHEN** `POST /api/matches/{id}/report/` is called
- **THEN** the view calls `MatchService.report_result(match_id, result_data)` and returns the serialized response; no ELO or state logic executes inside the view or serializer

#### Scenario: ELO update triggered by service
- **WHEN** a match result is reported
- **THEN** `EloService.update_ratings(match)` (or equivalent) is invoked from within the match service, not from the view

#### Scenario: Tournament state transition via service
- **WHEN** `POST /api/tournaments/{id}/start/` is called
- **THEN** the view calls `TournamentService.start(tournament_id)` and returns the result; tournament state validation logic is inside the service, not the view

### Requirement: Views are thin HTTP delegators
View methods (ViewSet actions) SHALL contain at most: request data extraction, a single service call, and response serialization. Any conditional logic beyond HTTP-level concerns (e.g., checking request.method) MUST live in the service.

#### Scenario: View contains no conditional business logic
- **WHEN** a developer reads any ViewSet action method
- **THEN** the method body contains only: input extraction from `request.data` or `request.query_params`, one service method call, and a `Response(serializer.data, status=...)` return

### Requirement: Service layer is independently unit-testable
Service methods MUST be callable in tests without an HTTP request context. They SHALL accept plain Python arguments (model instances, dicts, primitives) and return model instances or raise domain exceptions.

#### Scenario: Service tested without request
- **WHEN** a unit test calls `TournamentService.start(tournament_id=1)` directly
- **THEN** the test can assert on the returned value or raised exception without constructing an HTTP request or APIClient
