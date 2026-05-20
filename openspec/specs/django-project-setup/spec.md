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
Django REST Framework SHALL be installed (`rest_framework` in `INSTALLED_APPS`) with the following defaults set in `REST_FRAMEWORK`:
- `DEFAULT_AUTHENTICATION_CLASSES`: `['core.authentication.JavaJWTAuthentication']`
- `DEFAULT_PERMISSION_CLASSES`: `['rest_framework.permissions.IsAuthenticated']`
- `DEFAULT_PAGINATION_CLASS`: `'rest_framework.pagination.PageNumberPagination'`
- `PAGE_SIZE`: integer read from the `PAGE_SIZE` environment variable, defaulting to `20`

#### Scenario: Unauthenticated request is rejected by default
- **WHEN** a request with no `Authorization` header reaches any DRF view
- **THEN** the response status is `401 Unauthorized`

#### Scenario: PAGE_SIZE is configurable
- **WHEN** `PAGE_SIZE=50` is set in the environment
- **THEN** `settings.REST_FRAMEWORK['PAGE_SIZE']` equals `50`
