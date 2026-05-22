## 1. Project Scaffolding

- [x] 1.1 Generate the Spring Boot project at `auth-service/` via start.spring.io with Java 17, Maven, and dependencies: Spring Web, Spring Security, Spring Data JPA, PostgreSQL Driver
- [x] 1.2 Add `jjwt-api`, `jjwt-impl`, `jjwt-jackson` (0.12.x) and `flyway-core` to `pom.xml`
- [x] 1.3 Configure `application.properties` with `spring.datasource.*` (read from env), `spring.jpa.hibernate.ddl-auto=validate`, `server.port=${SERVER_PORT:8080}`
- [x] 1.4 Write Flyway migration `V1__create_refresh_tokens.sql` to create the `refresh_tokens` table (`id UUID PK`, `user_id UUID FK → users.id`, `token UUID UNIQUE NOT NULL`, `expires_at TIMESTAMP NOT NULL`, `revoked BOOLEAN NOT NULL DEFAULT false`)

## 2. Startup Guard for JWT_SECRET

- [x] 2.1 Write a failing test: application context fails to load when `JWT_SECRET` is absent or shorter than 32 characters
- [x] 2.2 Implement `JwtSecretValidator` `@Component` that reads `JWT_SECRET` in `@PostConstruct` and throws `IllegalStateException` (logged as FATAL) if the constraint is not met

## 3. Domain Model and Repository

- [x] 3.1 Write failing tests for `User` entity mapping to the existing `users` table columns (`id`, `email`, `password_hash`, `role`)
- [x] 3.2 Implement `User` JPA entity and `UserRepository` (JpaRepository)
- [x] 3.3 Write failing tests for `RefreshToken` entity mapping to `refresh_tokens`
- [x] 3.4 Implement `RefreshToken` JPA entity and `RefreshTokenRepository` with query methods: `findByToken(UUID)`, `revokeByToken(UUID)`

## 4. User Registration

- [x] 4.1 Write failing tests for `POST /auth/register`: 201 success, 409 duplicate email, 400 invalid role, 400 missing field
- [x] 4.2 Implement `RegisterRequest` DTO with Bean Validation (`@NotBlank`, `@Email`, custom `@ValidRole`)
- [x] 4.3 Implement `UserService.register()` using `BCryptPasswordEncoder` (strength 12)
- [x] 4.4 Implement `AuthController.register()` endpoint and global `@ControllerAdvice` for consistent error body format

## 5. Login and Token Issuance

- [x] 5.1 Write failing tests for `POST /auth/login`: 200 with token shape, 401 wrong password, 401 unknown email, 400 missing field
- [x] 5.2 Implement `JwtService.generateAccessToken(User)` using jjwt — claims: `sub`, `role`, `iat`, `exp`
- [x] 5.3 Implement `RefreshTokenService.createRefreshToken(User)` — generates UUID, persists row with `expires_at = now + 7 days`
- [x] 5.4 Implement `UserService.login()` and wire `AuthController.login()` endpoint

## 6. Refresh Token Rotation

- [x] 6.1 Write failing tests for `POST /auth/refresh`: 200 rotation, 401 revoked, 401 expired, 401 unknown token
- [x] 6.2 Implement `RefreshTokenService.rotate(UUID)` — find token, assert not revoked and not expired, mark old as `revoked = true`, create and return new token (atomic in `@Transactional`)
- [x] 6.3 Wire `AuthController.refresh()` endpoint

## 7. Token Validation Endpoint

- [x] 7.1 Write failing tests for `POST /auth/validate`: valid token → `{valid:true, email, role}`, expired → `{valid:false}`, tampered → `{valid:false}`, malformed → `{valid:false}`, missing field → 400
- [x] 7.2 Implement `JwtService.validate(String token)` returning a result object with the parsed claims or a failure flag — no DB lookup
- [x] 7.3 Wire `AuthController.validate()` endpoint; ensure Spring Security permits this path without authentication

## 8. Spring Security Configuration

- [x] 8.1 Write failing test confirming `/auth/register`, `/auth/login`, `/auth/validate`, `/auth/refresh` are all accessible without a bearer token
- [x] 8.2 Implement `SecurityConfig` disabling CSRF (stateless API), permitting the four `/auth/**` paths, and requiring authentication for all other routes
- [x] 8.3 Disable Spring Security's default form login and HTTP Basic

## 9. Integration Tests

- [x] 9.1 Write integration tests using an in-memory H2 datasource (or Testcontainers Postgres) covering the full login → validate flow
- [x] 9.2 Write integration test for the refresh token rotation sequence: login → refresh → reuse old token → expect 401
- [x] 9.3 Run `mvn test` and confirm all tests pass with no failures
