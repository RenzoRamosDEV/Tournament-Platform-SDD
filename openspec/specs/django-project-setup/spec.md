## ADDED Requirements

### Requirement: Django project and app scaffolding
The system SHALL be initialized with `django-admin startproject tournament_api` at the repository root, and a single app `core` created via `python manage.py startapp core`. The `core` app SHALL be listed in `INSTALLED_APPS`.

#### Scenario: App is registered
- **WHEN** Django starts
- **THEN** `core` appears in `django.apps.apps.get_app_configs()` without raising `ImproperlyConfigured`

### Requirement: PostgreSQL database backend
`settings.py` SHALL configure `DATABASES['default']` with `ENGINE = 'django.db.backends.postgresql'` using `psycopg2`. All connection parameters (NAME, USER, PASSWORD, HOST, PORT) SHALL be sourced from environment variables.

#### Scenario: Missing DB env var
- **WHEN** `DB_NAME` is not set in the environment and no default is defined
- **THEN** `python-decouple` raises `UndefinedValueError` before Django starts

### Requirement: CORS middleware as first entry
`corsheaders.middleware.CorsMiddleware` SHALL be the first item in `MIDDLEWARE`. `CORS_ALLOWED_ORIGINS` SHALL be populated by splitting the `CORS_ALLOWED_ORIGINS` environment variable on commas and stripping whitespace from each entry.

#### Scenario: Allowed origin passes preflight
- **WHEN** an HTTP OPTIONS request arrives with `Origin: http://localhost:3000` and `CORS_ALLOWED_ORIGINS` contains `http://localhost:3000`
- **THEN** the response includes the header `Access-Control-Allow-Origin: http://localhost:3000`

#### Scenario: Unlisted origin is blocked
- **WHEN** an HTTP OPTIONS request arrives with `Origin: http://evil.example.com` and `CORS_ALLOWED_ORIGINS` does not contain that origin
- **THEN** the response does NOT include an `Access-Control-Allow-Origin` header

### Requirement: DRF global configuration
Django REST Framework SHALL be installed (`rest_framework` in `INSTALLED_APPS`). The `REST_FRAMEWORK` settings dict SHALL have `DEFAULT_AUTHENTICATION_CLASSES` set to `['apps.users.authentication.BearerHeaderAuthentication']` (a header-only class that enables `401` responses — actual auth is delegated to `JwtAuthMiddleware`). `DEFAULT_PERMISSION_CLASSES`, `DEFAULT_PAGINATION_CLASS`, `PAGE_SIZE`, and other DRF settings are unchanged.

#### Scenario: Unauthenticated request is rejected by default
- **WHEN** a request with no `Authorization` header reaches any DRF view requiring authentication
- **THEN** the response status is `401 Unauthorized`

#### Scenario: PAGE_SIZE is configurable
- **WHEN** `PAGE_SIZE=50` is set in the environment
- **THEN** `settings.REST_FRAMEWORK['PAGE_SIZE']` equals `50`

### Requirement: AUTH_SERVICE_URL setting
`settings.py` SHALL define `AUTH_SERVICE_URL` read from the `AUTH_SERVICE_URL` environment variable with a default of `http://java-auth:8080`. The middleware MUST use this setting — the URL MUST NOT be hardcoded.

#### Scenario: AUTH_SERVICE_URL is configurable
- **WHEN** `AUTH_SERVICE_URL=http://localhost:8080` is set in the environment
- **THEN** `settings.AUTH_SERVICE_URL` equals `http://localhost:8080`

### Requirement: JwtAuthMiddleware wired into MIDDLEWARE
`JwtAuthMiddleware` (at `app.middleware.jwt_auth.JwtAuthMiddleware`) SHALL be added to `MIDDLEWARE` immediately after `CorsMiddleware`. Authentication via `djangorestframework-simplejwt` is not used.

#### Scenario: Middleware is active
- **WHEN** Django starts
- **THEN** `JwtAuthMiddleware` appears in the active middleware chain immediately after `CorsMiddleware`
