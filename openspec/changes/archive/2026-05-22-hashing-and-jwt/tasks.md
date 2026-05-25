## 1. Access Token Expiry Change

- [x] 1.1 Write a failing test asserting `expires_in` equals `900` in the login response (currently passes with `86400`)
- [x] 1.2 Update `jwt.access-token-expiration-seconds` from `86400` to `900` in `auth-service/src/main/resources/application.properties`
- [x] 1.3 Update the hardcoded `86400` literal in `RefreshTokenService.rotate()` to use `${jwt.access-token-expiration-seconds}` injected via `@Value` so it stays in sync with the property
- [x] 1.4 Update all test assertions that check `expires_in = 86400` to assert `expires_in = 900`
- [x] 1.5 Run `mvn test` and confirm all tests pass before proceeding

## 2. Logout — Failing Tests First

- [x] 2.1 Write failing test: `POST /auth/logout` with a valid refresh token returns `204 No Content`
- [x] 2.2 Write failing test: `POST /auth/logout` followed by `POST /auth/refresh` with same token returns `401`
- [x] 2.3 Write failing test: `POST /auth/logout` with unknown UUID returns `401` with `INVALID_REFRESH_TOKEN`
- [x] 2.4 Write failing test: `POST /auth/logout` with already-revoked token returns `401`
- [x] 2.5 Write failing test: `POST /auth/logout` is accessible without an `Authorization` header

## 3. Logout — Implementation

- [x] 3.1 Add `logout(String tokenString)` method to `RefreshTokenService` — find token, reject if not found/revoked/expired, set `revoked = true`, return void
- [x] 3.2 Add `LogoutRequest` DTO with `@NotBlank` `refreshToken` field and `@JsonProperty("refresh_token")`
- [x] 3.3 Add `POST /auth/logout` handler to `AuthController` returning `ResponseEntity<Void>` with status `204`
- [x] 3.4 Add `/auth/logout` to the permitted paths in `SecurityConfig`

## 4. Final Verification

- [x] 4.1 Run `mvn test` and confirm all tests pass with no failures
