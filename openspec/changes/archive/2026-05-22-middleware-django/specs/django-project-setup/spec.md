## MODIFIED Requirements

### Requirement: DRF global configuration
Django REST Framework SHALL be installed (`rest_framework` in `INSTALLED_APPS`). The `REST_FRAMEWORK` settings dict SHALL have `DEFAULT_AUTHENTICATION_CLASSES` set to an empty list `[]`. Authentication is handled by `JwtAuthMiddleware`, not DRF authentication classes. `DEFAULT_PERMISSION_CLASSES` and other DRF settings are unchanged.

#### Scenario: DRF authentication classes cleared
- **WHEN** Django starts with the updated settings
- **THEN** `settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` equals `[]`

## ADDED Requirements

### Requirement: AUTH_SERVICE_URL setting
`settings.py` SHALL define `AUTH_SERVICE_URL` read from the `AUTH_SERVICE_URL` environment variable with a default of `http://java-auth:8080`. The middleware MUST use this setting — the URL MUST NOT be hardcoded.

#### Scenario: AUTH_SERVICE_URL is configurable
- **WHEN** `AUTH_SERVICE_URL=http://localhost:8080` is set in the environment
- **THEN** `settings.AUTH_SERVICE_URL` equals `http://localhost:8080`

### Requirement: JwtAuthMiddleware wired into MIDDLEWARE
`JwtAuthMiddleware` (at `app.middleware.jwt_auth.JwtAuthMiddleware`) SHALL be added to `MIDDLEWARE` immediately after `CorsMiddleware`. `djangorestframework-simplejwt` SHALL be removed from `INSTALLED_APPS`, `REST_FRAMEWORK` authentication classes, and `requirements.txt`. All simplejwt URL patterns SHALL be removed from `urls.py`.

#### Scenario: Middleware is active
- **WHEN** Django starts
- **THEN** `JwtAuthMiddleware` appears in the active middleware chain

#### Scenario: simplejwt is absent
- **WHEN** Django starts
- **THEN** `rest_framework_simplejwt` does NOT appear in `INSTALLED_APPS` or any import
