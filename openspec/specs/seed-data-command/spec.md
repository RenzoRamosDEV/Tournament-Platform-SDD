## ADDED Requirements

### Requirement: seed_data command creates fixed development dataset
The management command `python manage.py seed_data` SHALL create:
- 20 users: 1 with `role='admin'`, 3 with `role='organizer'`, 16 with `role='player'`. All start with `elo=1000`.
- 6 teams, each owned by one of the organizer users.
- 3 tournaments: one with `status='finished'`, one `status='ongoing'`, one `status='open'`.
- Approximately 12 matches distributed across the three tournaments. Finished matches SHALL have corresponding `EloHistory` rows for each participating user.

#### Scenario: Command creates expected entity counts
- **WHEN** `python manage.py seed_data` is run against an empty database
- **THEN** `User.objects.count()` equals 20, `Team.objects.count()` equals 6, `Tournament.objects.count()` equals 3

#### Scenario: Finished matches have EloHistory
- **WHEN** `python manage.py seed_data` is run against an empty database
- **THEN** every `Match` with `status='finished'` has at least two `EloHistory` records (one per participating team's players)

### Requirement: seed_data is idempotent via get_or_create
All entity creation SHALL use `get_or_create` keyed on a stable identifier (`username` for users, `name` for teams/tournaments). Running the command multiple times SHALL NOT create duplicate records.

#### Scenario: Second run produces no duplicates
- **WHEN** `python manage.py seed_data` is run twice in succession
- **THEN** `User.objects.count()` remains 20 after both runs

### Requirement: --clear flag requires DEBUG=True
The command SHALL accept an optional `--clear` flag. When `--clear` is passed:
- If `settings.DEBUG` is `False`: the command SHALL print `"--clear is not allowed outside DEBUG mode."`, exit with a non-zero return code, and leave all data untouched.
- If `settings.DEBUG` is `True`: all rows in all `core` model tables SHALL be deleted before re-seeding.

#### Scenario: --clear blocked in production
- **GIVEN** `DEBUG=False`
- **WHEN** `python manage.py seed_data --clear` is run
- **THEN** the command exits with a non-zero return code and prints `"--clear is not allowed outside DEBUG mode."`, and no data is deleted

#### Scenario: --clear wipes and re-seeds in development
- **GIVEN** `DEBUG=True` and existing seed data
- **WHEN** `python manage.py seed_data --clear` is run
- **THEN** all existing core model data is deleted and 20 users, 6 teams, and 3 tournaments are recreated
