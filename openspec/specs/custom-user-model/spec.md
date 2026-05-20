## ADDED Requirements

### Requirement: Custom user model based on AbstractBaseUser
`core.models.User` SHALL extend `AbstractBaseUser` and `PermissionsMixin`. `settings.AUTH_USER_MODEL` SHALL be set to `'core.User'` before any migration is run.

#### Scenario: AUTH_USER_MODEL is set
- **WHEN** Django starts
- **THEN** `django.contrib.auth.get_user_model()` returns `core.models.User`

### Requirement: User model fields
The `User` model SHALL have exactly the following fields:

| Field | Details |
|---|---|
| `id` | `AutoField`, primary key |
| `username` | `CharField(max_length=150)`, `unique=True` |
| `email` | `EmailField`, `unique=True` |
| `password` | Managed by `AbstractBaseUser` (stored as `password` column with hash) |
| `role` | `CharField(max_length=20)`, choices `admin/organizer/player`, default `player` |
| `elo` | `IntegerField`, default `1000` |
| `avatar_url` | `URLField`, `blank=True, null=True` |
| `created_at` | `DateTimeField`, `auto_now_add=True` |

`USERNAME_FIELD` SHALL be `'email'`. `REQUIRED_FIELDS` SHALL be `['username']`.

#### Scenario: ELO defaults to 1000
- **WHEN** a `User` is created without specifying `elo`
- **THEN** `user.elo` equals `1000`

#### Scenario: Email is the login identifier
- **WHEN** `User.USERNAME_FIELD` is accessed
- **THEN** its value is `'email'`

### Requirement: Role field validation
The `role` field SHALL only accept `'admin'`, `'organizer'`, or `'player'`. Any other value SHALL raise a `ValidationError` when `full_clean()` is called.

#### Scenario: Valid role is accepted
- **WHEN** a `User` with `role='organizer'` has `full_clean()` called
- **THEN** no `ValidationError` is raised for the role field

#### Scenario: Invalid role is rejected
- **WHEN** a `User` with `role='referee'` has `full_clean()` called
- **THEN** a `ValidationError` is raised targeting the `role` field

### Requirement: UserManager for user creation
A custom `UserManager` extending `BaseUserManager` SHALL be set as `User.objects`. It SHALL provide:
- `create_user(email, username, password, **extra_fields)` — creates a regular user with `is_staff=False`, `is_superuser=False`
- `create_superuser(email, username, password, **extra_fields)` — creates a user with `is_staff=True`, `is_superuser=True`, `role='admin'`

#### Scenario: create_user sets is_staff=False
- **WHEN** `User.objects.create_user(email='a@b.com', username='a', password='pw')` is called
- **THEN** the resulting user has `is_staff=False` and `is_superuser=False`

#### Scenario: create_superuser sets is_staff=True
- **WHEN** `User.objects.create_superuser(email='admin@b.com', username='admin', password='pw')` is called
- **THEN** the resulting user has `is_staff=True`, `is_superuser=True`, and `role='admin'`
