## ADDED Requirements

### Requirement: Minimum 90% line coverage for both services
Both the Django+DRF backend and the Spring Boot auth service MUST achieve a minimum of **90% line coverage** as measured by their respective coverage tools (`coverage.py` for Django, JaCoCo for Spring Boot). Coverage MUST be measured on the final test run before merging.

#### Scenario: Django line coverage meets threshold
- **WHEN** `coverage run manage.py test` is executed followed by `coverage report`
- **THEN** the total line coverage is ≥ 90%; the build MUST fail if coverage drops below this threshold

#### Scenario: Spring Boot line coverage meets threshold
- **WHEN** Maven/Gradle runs with JaCoCo configured
- **THEN** the JaCoCo report shows ≥ 90% line coverage; the build MUST fail if coverage is below threshold

### Requirement: Minimum 95% mutation score for both services
Both services MUST achieve a mutation score of **≥ 95%** as measured by `mutmut` (Django) and PIT (Spring Boot). Any surviving mutant MUST be documented with a justification in a `mutation-notes.md` file co-located with the respective service's test suite.

#### Scenario: Django mutation score meets threshold
- **WHEN** `mutmut run` is executed on the Django service
- **THEN** the mutation score is ≥ 95%; any surviving mutant is documented in `django-api/mutation-notes.md` with a justification

#### Scenario: Spring Boot mutation score meets threshold
- **WHEN** PIT runs on the Spring Boot service
- **THEN** the mutation score is ≥ 95%; any surviving mutant is documented in `auth-service/mutation-notes.md` with a justification

### Requirement: Django unit tests mock the auth HTTP client
Django unit tests for service-layer logic MUST mock the HTTP client used to call the auth service. No Django unit test MUST require the Java/Spring Boot service to be running. The mock MUST cover at minimum: successful validation, timeout, 5xx error, and 401/403 responses.

#### Scenario: Auth service mock covers timeout case
- **WHEN** a Django unit test simulates an auth service timeout
- **THEN** the test patches the HTTP client to raise `requests.exceptions.Timeout` and asserts the middleware returns `503`; no real network call is made

#### Scenario: All auth service response types covered
- **WHEN** the Django unit test suite runs
- **THEN** there are tests covering: successful `{ "valid": true }`, timeout, HTTP 500, `{ "valid": false }` (401), and HTTP 403 responses from the auth service

### Requirement: Spring Boot unit tests mock repositories
Spring Boot unit tests for service-layer logic MUST use mocked repositories (Mockito). No Spring Boot unit test MUST require a live database connection.

#### Scenario: Service test runs without a database
- **WHEN** a Spring Boot service unit test runs
- **THEN** all `@Repository` dependencies are mocked with Mockito; the test does not require `@DataJpaTest` or a real datasource
