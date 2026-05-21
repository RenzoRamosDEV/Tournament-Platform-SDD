"""
Integration tests requiring a live PostgreSQL >= 15 instance.
Run with: pytest tests/test_integration_pg.py -m integration --ds=config.pg_settings
"""
import pytest
from django.db import connection


@pytest.fixture(scope="module")
def db_cursor(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            yield cursor


@pytest.mark.integration
@pytest.mark.django_db
class DomainTablesTest:
    """After migration, all 6 domain tables must exist."""

    EXPECTED_TABLES = {
        "users",
        "teams",
        "team_members",
        "tournaments",
        "tournament_teams",
        "matches",
    }

    def test_all_domain_tables_exist(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                """
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert self.EXPECTED_TABLES <= tables, (
            f"Missing tables: {self.EXPECTED_TABLES - tables}"
        )


@pytest.mark.integration
@pytest.mark.django_db
class ConstraintsTest:
    """Check constraints and unique constraints must be present after migration."""

    EXPECTED_CHECK_CONSTRAINTS = {
        "users_role_valid",
        "tournaments_status_valid",
        "tournaments_format_valid",
        "tournaments_max_teams_positive",
        "tournaments_end_date_gte_start_date",
        "matches_status_valid",
        "matches_winner_valid",
    }

    EXPECTED_UNIQUE_CONSTRAINTS = {
        "team_members_pk",
        "tournament_teams_pk",
    }

    def test_check_constraints_exist(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'CHECK'
                  AND table_schema = 'public'
                """
            )
            names = {row[0] for row in cursor.fetchall()}
        missing = self.EXPECTED_CHECK_CONSTRAINTS - names
        assert not missing, f"Missing CHECK constraints: {missing}"

    def test_unique_constraints_exist(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                  AND table_schema = 'public'
                """
            )
            names = {row[0] for row in cursor.fetchall()}
        missing = self.EXPECTED_UNIQUE_CONSTRAINTS - names
        assert not missing, f"Missing UNIQUE constraints: {missing}"


@pytest.mark.integration
@pytest.mark.django_db
class IndexesTest:
    """Required indexes must be present in pg_indexes after migration."""

    EXPECTED_INDEXES = {
        "users_elo_desc_idx",
        "matches_tournament_idx",
        "matches_played_at_idx",
    }

    def test_indexes_exist(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                """
            )
            names = {row[0] for row in cursor.fetchall()}
        missing = self.EXPECTED_INDEXES - names
        assert not missing, f"Missing indexes: {missing}"


@pytest.mark.integration
@pytest.mark.django_db
class MatchWinnerConstraintTest:
    """INSERT with invalid winner_team_id must raise IntegrityError naming matches_winner_valid."""

    def test_invalid_winner_raises_integrity_error(self):
        from django.db import IntegrityError
        from apps.users.models import User
        from apps.teams.models import Team
        from apps.tournaments.models import Tournament
        import datetime

        user = User.objects.create_user(username="t_user", password="pw")
        team_a = Team.objects.create(name="Team A", owner=user)
        team_b = Team.objects.create(name="Team B", owner=user)
        team_c = Team.objects.create(name="Team C", owner=user)
        tournament = Tournament.objects.create(
            name="T1",
            format="single_elim",
            max_teams=4,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
        )

        with pytest.raises(IntegrityError) as exc_info:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO matches
                        (tournament_id, team_a_id, team_b_id, winner_team_id, score_a, score_b, status)
                    VALUES (%s, %s, %s, %s, 0, 0, 'finished')
                    """,
                    [tournament.id, team_a.id, team_b.id, team_c.id],
                )

        assert "matches_winner_valid" in str(exc_info.value)
