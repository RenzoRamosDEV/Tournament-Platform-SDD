## ADDED Requirements

### Requirement: CORS_ALLOWED_ORIGINS environment variable
`settings.py` SHALL read `CORS_ALLOWED_ORIGINS` from the environment using `python-decouple`. The value SHALL be parsed as a comma-separated string and split into a Python list, with whitespace stripped from each entry. The default value when the variable is absent SHALL be `'http://localhost:3000,http://localhost:5073'`.

#### Scenario: CORS origins parsed correctly
- **WHEN** `CORS_ALLOWED_ORIGINS=http://localhost:3000, http://localhost:5073` is set in the environment (with a space after the comma)
- **THEN** `settings.CORS_ALLOWED_ORIGINS` equals `['http://localhost:3000', 'http://localhost:5073']`

#### Scenario: Default origins apply when variable is absent
- **WHEN** `CORS_ALLOWED_ORIGINS` is not set in the environment
- **THEN** `settings.CORS_ALLOWED_ORIGINS` equals `['http://localhost:3000', 'http://localhost:5073']`

### Requirement: PAGE_SIZE environment variable
`settings.py` SHALL read `PAGE_SIZE` from the environment as an integer using `python-decouple`. The default value when absent SHALL be `20`. This value SHALL be used as `REST_FRAMEWORK['PAGE_SIZE']`.

#### Scenario: Custom PAGE_SIZE is applied
- **WHEN** `PAGE_SIZE=50` is set in the environment
- **THEN** `settings.REST_FRAMEWORK['PAGE_SIZE']` equals `50`

#### Scenario: PAGE_SIZE defaults to 20
- **WHEN** `PAGE_SIZE` is not set in the environment
- **THEN** `settings.REST_FRAMEWORK['PAGE_SIZE']` equals `20`

### Requirement: Environment-variable-driven database configuration
Django's `settings.py` SHALL read all database connection parameters exclusively from environment variables. Hardcoded credential values MUST NOT exist in any committed file. `python-decouple` SHALL be used to load a `.env` file from the project root when present (replacing `python-dotenv`).

#### Scenario: All variables set — Django connects
- **WHEN** `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, and `DB_PORT` are all set in the environment
- **THEN** Django reads them and connects to PostgreSQL without error

#### Scenario: Optional variables absent — defaults apply
- **WHEN** `DB_HOST` and `DB_PORT` are not set
- **THEN** Django uses `localhost` and `5432` respectively

---

### Requirement: Hard failure on missing required variables
The system SHALL raise an error at settings-load time (before any database operation) when `DB_USER` or `DB_PASSWORD` is absent from the environment. The error message MUST identify the missing variable by name.

#### Scenario: DB_USER missing
- **WHEN** `DB_USER` is not set in the environment or `.env` file
- **THEN** Django raises `KeyError: 'DB_USER'` during settings import; no database connection is attempted

#### Scenario: DB_PASSWORD missing
- **WHEN** `DB_PASSWORD` is not set in the environment or `.env` file
- **THEN** Django raises `KeyError: 'DB_PASSWORD'` during settings import; no database connection is attempted

---

### Requirement: .env.example provided and .env gitignored
The repository SHALL include a `.env.example` file listing all required variables with placeholder values and inline comments. A `.env` file containing real credentials MUST be listed in `.gitignore` and MUST NOT be committed. The required variables are: `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `CORS_ALLOWED_ORIGINS`, `PAGE_SIZE`.

#### Scenario: .env.example contains all required keys
- **WHEN** `.env.example` is read
- **THEN** it contains exactly the keys: `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `CORS_ALLOWED_ORIGINS`, `PAGE_SIZE`, each with a placeholder value and a one-line comment

#### Scenario: .env is gitignored
- **WHEN** a `.env` file is created at the project root
- **THEN** `git status` does not list it as a tracked or untracked file

---

### Requirement: test_settings.py unaffected — SQLite in-memory preserved
The `test_settings.py` override MUST continue to set `DATABASES` to SQLite in-memory so that unit tests remain fast and require no running PostgreSQL instance.

#### Scenario: Unit tests run without PostgreSQL
- **WHEN** `pytest tests/` is run with `DJANGO_SETTINGS_MODULE=tournament_platform.test_settings`
- **THEN** all tests pass using SQLite in-memory; no PostgreSQL connection is made

---

### Requirement: pg_settings.py enables PostgreSQL integration testing
A `pg_settings.py` file SHALL exist in `tournament_platform/` that inherits all settings from `settings.py` without overriding `DATABASES`. This file is the designated settings module for running the integration test suite against PostgreSQL.

#### Scenario: pg_settings inherits env-var DB config
- **WHEN** `DJANGO_SETTINGS_MODULE=tournament_platform.pg_settings` is set and `.env` provides credentials
- **THEN** Django connects to PostgreSQL using the env-var values
