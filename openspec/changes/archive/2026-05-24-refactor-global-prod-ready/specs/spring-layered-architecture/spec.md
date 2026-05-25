## ADDED Requirements

### Requirement: Strict three-layer architecture
The Spring Boot auth service MUST follow a strict three-layer structure:
- **Controllers**: Handle HTTP binding and delegation only. MUST NOT contain any business logic. MUST call service methods and return their results.
- **Services**: Contain all business logic. MUST NOT directly access repositories of other aggregate roots unless there is no alternative. MUST be the sole layer making business decisions.
- **Repositories**: Are the sole data-access point. MUST NOT contain any business logic or computed behavior beyond standard JPA query methods.

No business logic is permitted in Controllers or Repositories.

#### Scenario: Controller delegates entirely to service
- **WHEN** a developer reads any `@RestController` method
- **THEN** the method body contains only: parameter extraction from the request, a single service method call, and returning the result (possibly with a `ResponseEntity` wrapper); no conditional logic based on business state

#### Scenario: Repository contains no business logic
- **WHEN** a developer reads any `@Repository` interface
- **THEN** it contains only method declarations (JPA query methods, `@Query` annotations) and no `if` statements, state validation, or computation

#### Scenario: Service unit test exercises business logic
- **WHEN** a unit test for a service class runs with all repositories mocked
- **THEN** the test can fully verify business logic (token validation, state transitions, user lookup) without a database or HTTP context

### Requirement: No cross-layer dependency violations
Controllers MUST NOT import or use Repository interfaces directly. Repositories MUST NOT import or use Service classes. This enforces a strict top-down dependency: Controller → Service → Repository.

#### Scenario: Controller imports only service interfaces
- **WHEN** a static analysis tool (or code review) inspects any `@RestController` class
- **THEN** the class imports only service interfaces/classes and standard Spring/HTTP types; no `Repository` import is present
