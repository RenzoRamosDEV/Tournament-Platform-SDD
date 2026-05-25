"""
Integration tests for raw SQL query practice.

Run with:
    pytest tests/tournaments/test_sql_queries.py -m integration --ds=config.pg_settings
"""
import datetime

import pytest
from django.db import connection

from apps.teams.models import Team
from apps.tournaments.models import Match, Tournament
from apps.users.models import User


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def two_players(db):
    """Two users with distinct, known ELO values."""
    winner = User.objects.create_user(username="sql_winner", email="sql_winner@test.com", password="pw", elo=1200)
    loser = User.objects.create_user(username="sql_loser", email="sql_loser@test.com", password="pw", elo=1000)
    return winner, loser


@pytest.fixture
def two_teams(two_players):
    """Two teams owned by the two players."""
    winner, loser = two_players
    team_a = Team.objects.create(name="sql_team_a", owner=winner)
    team_b = Team.objects.create(name="sql_team_b", owner=loser)
    return team_a, team_b


@pytest.fixture
def tournament(db):
    creator = User.objects.create_user(
        username="sql_creator", email="sql_creator@test.com", password="pw"
    )
    return Tournament.objects.create(
        name="sql_tournament",
        format="single_elimination",
        max_teams=4,
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 1, 31),
        created_by=creator,
    )


@pytest.fixture
def match(two_teams, tournament):
    team_a, team_b = two_teams
    return Match.objects.create(
        tournament=tournament,
        team_a=team_a,
        team_b=team_b,
        status="scheduled",
    )


# ---------------------------------------------------------------------------
# 1. Index tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class IndexTest:
    """users_elo_desc_idx must exist and be used by the ranking query."""

    def test_elo_index_exists(self):
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename  = 'users'
                  AND indexname  = 'users_elo_desc_idx'
                """
            )
            row = cur.fetchone()
        assert row is not None, "Index users_elo_desc_idx not found on users table"

    def test_elo_index_not_duplicated(self):
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename  = 'users'
                  AND indexdef   LIKE '%elo%'
                """
            )
            count = cur.fetchone()[0]
        assert count == 1, f"Expected exactly 1 elo index, found {count}"


# ---------------------------------------------------------------------------
# 2. Leaderboard ranking query
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class LeaderboardQueryTest:
    def _seed_users(self, n: int, base_elo: int = 1000):
        for i in range(n):
            User.objects.get_or_create(
                username=f"rank_user_{i}",
                defaults={"email": f"rank_user_{i}@test.com", "elo": base_elo + i},
            )
            User.objects.filter(username=f"rank_user_{i}").update(elo=base_elo + i)

    def test_returns_exactly_50_rows(self, db):
        self._seed_users(60)
        with connection.cursor() as cur:
            cur.execute("SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50")
            rows = cur.fetchall()
        assert len(rows) == 50

    def test_rows_ordered_by_elo_descending(self, db):
        self._seed_users(10)
        with connection.cursor() as cur:
            cur.execute("SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50")
            rows = cur.fetchall()
        elo_values = [r[1] for r in rows]
        assert elo_values == sorted(elo_values, reverse=True)

    def test_uses_elo_index(self, db):
        self._seed_users(60)
        with connection.cursor() as cur:
            cur.execute("EXPLAIN SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50")
            plan = "\n".join(r[0] for r in cur.fetchall())
        assert "users_elo_desc_idx" in plan, f"Index not used in query plan:\n{plan}"


# ---------------------------------------------------------------------------
# 3. Team win aggregation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class TeamWinsQueryTest:
    ALL_TIME_SQL = """
        SELECT t.name AS team_name,
               COUNT(m.id) AS win_count
        FROM teams t
        JOIN matches m ON m.winner_team_id = t.id
        GROUP BY t.id, t.name
        ORDER BY win_count DESC
    """
    PER_TOURNAMENT_SQL = """
        SELECT t.name AS team_name,
               COUNT(m.id) AS win_count
        FROM teams t
        JOIN matches m ON m.winner_team_id = t.id
        WHERE m.tournament_id = %s
        GROUP BY t.id, t.name
        ORDER BY win_count DESC
    """

    def _make_tournament(self, name):
        creator = User.objects.create_user(
            username=f"cr_{name}", email=f"cr_{name}@test.com", password="pw"
        )
        return Tournament.objects.create(
            name=name, format="single_elimination", max_teams=4,
            start_date=datetime.date(2025, 2, 1), end_date=datetime.date(2025, 2, 28),
            created_by=creator,
        )

    def test_all_time_wins_ordered_descending(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        t2 = self._make_tournament("sql_t2")
        for _ in range(3):
            Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b, winner_team=team_a, status="finished")
        for _ in range(2):
            Match.objects.create(tournament=t2, team_a=team_a, team_b=team_b, winner_team=team_b, status="finished")
        with connection.cursor() as cur:
            cur.execute(self.ALL_TIME_SQL)
            rows = cur.fetchall()
        counts = [r[1] for r in rows]
        a_count = dict(rows)["sql_team_a"]
        b_count = dict(rows)["sql_team_b"]
        assert a_count == 3
        assert b_count == 2
        assert counts == sorted(counts, reverse=True)

    def test_per_tournament_excludes_other_tournaments(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        t2 = self._make_tournament("sql_t3")
        for _ in range(2):
            Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b, winner_team=team_a, status="finished")
        for _ in range(4):
            Match.objects.create(tournament=t2, team_a=team_a, team_b=team_b, winner_team=team_a, status="finished")
        with connection.cursor() as cur:
            cur.execute(self.PER_TOURNAMENT_SQL, [tournament.id])
            rows = dict(cur.fetchall())
        assert rows.get("sql_team_a") == 2, f"Expected 2, got {rows}"
        assert "sql_team_b" not in rows

    def test_team_with_zero_wins_excluded(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        Match.objects.create(tournament=tournament, team_a=team_a, team_b=team_b, winner_team=team_a, status="finished")
        with connection.cursor() as cur:
            cur.execute(self.ALL_TIME_SQL)
            rows = dict(cur.fetchall())
        assert "sql_team_b" not in rows


# ---------------------------------------------------------------------------
# 4. Dual team-name match listing
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class MatchListingQueryTest:
    SQL = """
        SELECT m.id, ta.name, tb.name, m.winner_team_id, m.played_at
        FROM matches m
        JOIN teams ta ON m.team_a_id = ta.id
        JOIN teams tb ON m.team_b_id = tb.id
    """

    def test_resolves_both_team_names(self, db, match):
        with connection.cursor() as cur:
            cur.execute(self.SQL + " WHERE m.id = %s", [match.id])
            row = cur.fetchone()
        assert row is not None
        match_id, a_name, b_name, winner_team_id, played_at = row
        assert a_name == "sql_team_a"
        assert b_name == "sql_team_b"

    def test_result_columns_present(self, db, match):
        with connection.cursor() as cur:
            cur.execute(self.SQL + " WHERE m.id = %s", [match.id])
            description = [d[0] for d in cur.description]
        assert len(description) == 5


# ---------------------------------------------------------------------------
# 5. Transactional ELO recalculation
# ---------------------------------------------------------------------------


def _elo_new(my_elo: int, opp_elo: int, won: bool) -> int:
    expected = 1.0 / (1 + 10 ** ((opp_elo - my_elo) / 400.0))
    result = 1 if won else 0
    return round(my_elo + 32 * (result - expected))


def _run_elo_transaction(match_id, winner_team_id, winner_user_id, loser_user_id, winner_elo, loser_elo):
    new_winner_elo = _elo_new(winner_elo, loser_elo, won=True)
    new_loser_elo = _elo_new(loser_elo, winner_elo, won=False)
    with connection.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("UPDATE matches SET winner_team_id = %s WHERE id = %s", [winner_team_id, match_id])
            cur.execute("UPDATE users SET elo = %s WHERE id = %s", [new_winner_elo, winner_user_id])
            cur.execute("UPDATE users SET elo = %s WHERE id = %s", [new_loser_elo, loser_user_id])
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise


@pytest.mark.integration
@pytest.mark.django_db
class EloTransactionTest:
    def test_winner_elo_increases(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        _run_elo_transaction(match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo)
        winner.refresh_from_db()
        assert winner.elo > 1200

    def test_loser_elo_decreases(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        _run_elo_transaction(match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo)
        loser.refresh_from_db()
        assert loser.elo < 1000

    def test_winner_team_id_set(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        _run_elo_transaction(match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo)
        match.refresh_from_db()
        assert match.winner_team_id == team_a.id

    def test_rollback_leaves_rows_unchanged(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        original_winner_elo = winner.elo
        original_loser_elo = loser.elo
        with pytest.raises(Exception):
            with connection.cursor() as cur:
                cur.execute("BEGIN")
                try:
                    cur.execute("UPDATE matches SET winner_team_id = %s WHERE id = %s", [team_a.id, match.id])
                    cur.execute("UPDATE users SET elo = %s WHERE id = %s", [9999, winner.id])
                    cur.execute("SELECT 1/0")
                    cur.execute("COMMIT")
                except Exception:
                    cur.execute("ROLLBACK")
                    raise
        winner.refresh_from_db()
        loser.refresh_from_db()
        match.refresh_from_db()
        assert winner.elo == original_winner_elo
        assert loser.elo == original_loser_elo
        assert match.winner_team_id is None
