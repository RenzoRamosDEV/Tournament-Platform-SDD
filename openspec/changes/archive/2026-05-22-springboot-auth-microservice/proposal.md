## Why

Django currently owns both domain logic and authentication token issuance, mixing responsibilities that belong in separate services. Moving auth to a dedicated Spring Boot microservice establishes a clean boundary: Django handles tournament data, while the auth service owns all identity and credential concerns.

## What Changes

- A new Spring Boot (Java 17, Maven) project is introduced as `auth-service/` at the repo root
- The auth service connects to the same PostgreSQL database as Django but reads/writes only the `users` table (`id`, `email`, `password_hash`, `role`) and a new `refresh_tokens` table
- Four new REST endpoints are exposed: `POST /auth/register`, `POST /auth/login`, `POST /auth/validate`, `POST /auth/refresh`
- JWTs are issued by Spring Boot using HMAC-SHA256 with a 24-hour access token expiry; refresh tokens (UUID) are stored in the DB with a 7-day expiry and rotation-on-use
- Passwords are stored with bcrypt (cost factor 12); no PBKDF2 compatibility is needed (no existing users)
- Django JWT issuance is **not** changed in this task — that migration is a follow-up
- **BREAKING**: The `users` table gains a new sibling table `refresh_tokens`; schema ownership must be coordinated with Django migrations

## Capabilities

### New Capabilities
- `jwt-token-issuance`: Issues HMAC-SHA256 signed JWTs (access + refresh) upon successful credential verification
- `user-credential-management`: Registration and bcrypt-hashed password storage for users with roles `ADMIN`, `ORGANIZER`, `PLAYER`
- `token-validation-endpoint`: Stateless JWT verification endpoint consumed by Django and other services to validate bearer tokens without shared state

### Modified Capabilities

## Impact

- **New project**: `auth-service/` — standalone Spring Boot application, port 8080
- **Database**: Shared PostgreSQL DB; adds `refresh_tokens` table; reads existing `users` table
- **Environment**: Requires `JWT_SECRET` (min 32 chars) and `DATABASE_URL` env vars; service refuses to start without `JWT_SECRET`
- **Django**: Not modified in this task; `POST /auth/validate` is the integration point for future Django middleware changes
- **Dependencies added**: `spring-boot-starter-web`, `spring-boot-starter-security`, `spring-boot-starter-data-jpa`, `postgresql` driver, `jjwt` (JWT library)
