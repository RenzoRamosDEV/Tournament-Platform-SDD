## ADDED Requirements

### Requirement: Team model
`core.models.Team` SHALL define: `id` (AutoField PK), `name` (CharField max_length=100, unique=True), `owner` (ForeignKey to `User`, on_delete=PROTECT), `created_at` (DateTimeField auto_now_add). `db_table` SHALL be `'teams'`.

#### Scenario: Deleting a user with owned teams is blocked
- **WHEN** a `User` who owns a `Team` is deleted
- **THEN** a `ProtectedError` is raised and the user is NOT deleted

### Requirement: TeamMember bridge table
`core.models.TeamMember` SHALL define: `team` (ForeignKey to `Team`, on_delete=CASCADE), `user` (ForeignKey to `User`, on_delete=CASCADE), `joined_at` (DateTimeField auto_now_add). `Meta.unique_together` SHALL be `[('team', 'user')]`. `db_table` SHALL be `'team_members'`.

#### Scenario: Duplicate membership is rejected
- **WHEN** a second `TeamMember` with the same `team` and `user` is saved
- **THEN** an `IntegrityError` is raised

### Requirement: Tournament model
`core.models.Tournament` SHALL define: `id` (AutoField PK), `name` (CharField max_length=200), `status` (CharField, choices: `draft/open/ongoing/finished`, default `draft`), `format` (CharField, choices: `single_elimination/round_robin`), `max_teams` (PositiveIntegerField), `start_date` (DateField), `end_date` (DateField), `created_by` (ForeignKey to `User`, on_delete=PROTECT). `db_table` SHALL be `'tournaments'`.

#### Scenario: Default status is draft
- **WHEN** a `Tournament` is created without specifying `status`
- **THEN** `tournament.status` equals `'draft'`

### Requirement: TournamentTeam inscription table
`core.models.TournamentTeam` SHALL define: `tournament` (ForeignKey to `Tournament`, on_delete=CASCADE), `team` (ForeignKey to `Team`, on_delete=CASCADE), `registered_at` (DateTimeField auto_now_add). `Meta.unique_together` SHALL be `[('tournament', 'team')]`. `db_table` SHALL be `'tournament_teams'`.

#### Scenario: Duplicate registration is rejected
- **WHEN** the same team is registered to the same tournament twice
- **THEN** an `IntegrityError` is raised

### Requirement: Match model
`core.models.Match` SHALL define: `id` (AutoField PK), `tournament` (ForeignKey to `Tournament`, on_delete=CASCADE), `team_a` (ForeignKey to `Team`, on_delete=PROTECT, related_name=`'matches_as_a'`), `team_b` (ForeignKey to `Team`, on_delete=PROTECT, related_name=`'matches_as_b'`), `winner_team` (ForeignKey to `Team`, null=True, blank=True, on_delete=PROTECT, related_name=`'won_matches'`), `score_a` (IntegerField default=0), `score_b` (IntegerField default=0), `status` (CharField, choices: `scheduled/ongoing/finished`, default `scheduled`), `played_at` (DateTimeField null=True, blank=True). `db_table` SHALL be `'matches'`.

#### Scenario: Default status is scheduled
- **WHEN** a `Match` is created without specifying `status`
- **THEN** `match.status` equals `'scheduled'`

#### Scenario: winner_team is nullable for unfinished match
- **WHEN** a `Match` with `status='scheduled'` is saved with `winner_team=None`
- **THEN** it saves successfully

### Requirement: Match integrity validation
`Match.clean()` SHALL enforce: when `status` is `'finished'`, `winner_team` MUST NOT be `None` and MUST be either `team_a` or `team_b`. Violations SHALL raise `ValidationError`. No draws are possible.

#### Scenario: Finished match without winner fails clean
- **WHEN** a `Match` with `status='finished'` and `winner_team=None` has `full_clean()` called
- **THEN** a `ValidationError` is raised

#### Scenario: Finished match with non-participant winner fails clean
- **WHEN** a `Match` with `status='finished'` and `winner_team` set to a team that is neither `team_a` nor `team_b` has `full_clean()` called
- **THEN** a `ValidationError` is raised

#### Scenario: Finished match with valid winner passes clean
- **WHEN** a `Match` with `status='finished'` and `winner_team=team_a` has `full_clean()` called
- **THEN** no `ValidationError` is raised

### Requirement: EloHistory model
`core.models.EloHistory` SHALL define: `id` (AutoField PK), `user` (ForeignKey to `User`, on_delete=CASCADE), `match` (ForeignKey to `Match`, on_delete=CASCADE), `elo_before` (IntegerField), `elo_after` (IntegerField), `changed_at` (DateTimeField auto_now_add). `db_table` SHALL be `'elo_history'`.

#### Scenario: EloHistory is deleted when user is deleted
- **WHEN** a `User` is deleted
- **THEN** all `EloHistory` records for that user are also deleted (CASCADE)
