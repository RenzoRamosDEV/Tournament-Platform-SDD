## ADDED Requirements

### Requirement: User registration
The auth service SHALL accept a registration request containing `email`, `password`, and `role`. It MUST store the user in the `users` table with a bcrypt-hashed password (cost factor 12). The `role` field MUST be one of `ADMIN`, `ORGANIZER`, or `PLAYER`. The `email` field MUST be unique across all users.

#### Scenario: Successful registration
- **WHEN** `POST /auth/register` is called with `{ "email": "player@example.com", "password": "StrongPass1!", "role": "PLAYER" }` and the email does not exist
- **THEN** the service returns `201 Created` with `{ "id": "<uuid>", "email": "player@example.com", "role": "PLAYER" }` and stores a bcrypt hash in `password_hash`

#### Scenario: Duplicate email
- **WHEN** `POST /auth/register` is called with an email that already exists in the `users` table
- **THEN** the service returns `409 Conflict` with `{ "error": "EMAIL_ALREADY_EXISTS", "message": "An account with this email already exists." }`

#### Scenario: Invalid role value
- **WHEN** `POST /auth/register` is called with `role` set to a value not in `[ADMIN, ORGANIZER, PLAYER]`
- **THEN** the service returns `400 Bad Request` with `{ "error": "VALIDATION_ERROR", "message": "role must be one of: ADMIN, ORGANIZER, PLAYER" }`

#### Scenario: Missing required field
- **WHEN** `POST /auth/register` is called with any of `email`, `password`, or `role` absent from the request body
- **THEN** the service returns `400 Bad Request` with `{ "error": "VALIDATION_ERROR", "message": "<field> is required" }`

### Requirement: Credential verification on login
The auth service SHALL verify a user's credentials by looking up the email in the `users` table and comparing the provided password against the stored bcrypt hash. The error response MUST NOT reveal which field (email or password) was incorrect.

#### Scenario: Successful login
- **WHEN** `POST /auth/login` is called with a valid email and matching password
- **THEN** the service returns `200 OK` with `{ "access_token": "<jwt>", "refresh_token": "<uuid>", "token_type": "Bearer", "expires_in": 86400 }`

#### Scenario: Wrong password
- **WHEN** `POST /auth/login` is called with a valid email and an incorrect password
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect." }`

#### Scenario: Unknown email
- **WHEN** `POST /auth/login` is called with an email that does not exist in the `users` table
- **THEN** the service returns `401 Unauthorized` with `{ "error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect." }`

#### Scenario: Missing login field
- **WHEN** `POST /auth/login` is called with `email` or `password` absent
- **THEN** the service returns `400 Bad Request` with `{ "error": "VALIDATION_ERROR", "message": "<field> is required" }`
