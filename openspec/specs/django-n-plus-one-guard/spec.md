## ADDED Requirements

### Requirement: O(1) query count on list endpoints
All list endpoints that traverse foreign-key or many-to-many relations MUST use `select_related` or `prefetch_related` such that the total number of SQL queries issued per request does NOT grow with the number of returned objects. The query count MUST be constant (O(1)) with respect to result set size.

Affected endpoints and their required eager-load strategy:

| Endpoint | Relation | Strategy |
|---|---|---|
| `GET /api/tournaments/` | teams M2M | `prefetch_related("teams")` |
| `GET /api/matches/` | tournament FK, teams M2M | `select_related("tournament")` + `prefetch_related("teams")` |
| `GET /api/teams/` | tournament M2M, users M2M | `prefetch_related("tournaments", "members")` |
| `GET /api/users/` | team M2M | `prefetch_related("teams")` |

#### Scenario: Tournament list query count is constant
- **WHEN** `GET /api/tournaments/` is called with 50 tournaments each linked to 10 teams
- **THEN** the total number of SQL queries issued is the same as when called with 1 tournament linked to 1 team (query count does not scale with result size)

#### Scenario: Match list does not issue per-match queries
- **WHEN** `GET /api/matches/` returns 20 matches each with 2 teams and a tournament
- **THEN** no additional SQL queries are issued per match; all related data is fetched in a fixed number of queries

### Requirement: Query count assertions in tests
Each list endpoint's integration test MUST include at least one `assertNumQueries` (or equivalent `CaptureQueriesContext`) assertion that verifies the query count does not exceed the expected constant.

#### Scenario: Test catches N+1 regression
- **WHEN** a developer removes `prefetch_related` from a queryset and runs the test suite
- **THEN** the corresponding `assertNumQueries` test fails, preventing the regression from merging
