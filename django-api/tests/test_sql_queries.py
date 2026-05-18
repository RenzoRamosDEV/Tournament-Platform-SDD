"""
Integration tests for raw SQL query practice.

Run with:
    pytest tests/test_sql_queries.py -m integration --ds=tournament_platform.pg_settings
"""
import datetime

import pytest
from django.db import connection

from core.models import Match, Team, Tournament, User


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def two_players(db):
    """Two users with distinct, known ELO values."""
    winner = User.objects.create_user(username="sql_winner", password="pw", elo=1200)
    loser = User.objects.create_user(username="sql_loser", password="pw", elo=1000)
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
    return Tournament.objects.create(
        name="sql_tournament",
        format="single_elim",
        max_teams=4,
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(2025, 1, 31),
    )


@pytest.fixture
def match(two_teams, tournament):
    team_a, team_b = two_teams
    return Match.objects.create(
        tournament=tournament,
        team_a=team_a,
        team_b=team_b,
        status="pending",
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
        """Only one index on elo should exist — no stale copies."""
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
    """Ranking query returns top-50 users ordered by elo DESC."""

    def _seed_users(self, n: int, base_elo: int = 1000):
        for i in range(n):
            User.objects.get_or_create(
                username=f"rank_user_{i}",
                defaults={"elo": base_elo + i},
            )
            User.objects.filter(username=f"rank_user_{i}").update(elo=base_elo + i)

    def test_returns_exactly_50_rows(self, db):
        self._seed_users(60)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50"
            )
            rows = cur.fetchall()
        assert len(rows) == 50

    def test_rows_ordered_by_elo_descending(self, db):
        self._seed_users(10)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50"
            )
            rows = cur.fetchall()
        elo_values = [r[1] for r in rows]
        assert elo_values == sorted(elo_values, reverse=True)

    def test_uses_elo_index(self, db):
        """EXPLAIN output must reference users_elo_desc_idx."""
        self._seed_users(60)
        with connection.cursor() as cur:
            cur.execute(
                "EXPLAIN SELECT username, elo FROM users ORDER BY elo DESC LIMIT 50"
            )
            plan = "\n".join(r[0] for r in cur.fetchall())
        assert "users_elo_desc_idx" in plan, (
            f"Index not used in query plan:\n{plan}"
        )


# ---------------------------------------------------------------------------
# 3. Team win aggregation
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class TeamWinsQueryTest:
    """All-time and per-tournament win counts."""

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

    def test_all_time_wins_ordered_descending(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        t2 = Tournament.objects.create(
            name="sql_t2",
            format="single_elim",
            max_teams=4,
            start_date=datetime.date(2025, 2, 1),
            end_date=datetime.date(2025, 2, 28),
        )
        for _ in range(3):
            Match.objects.create(
                tournament=tournament, team_a=team_a, team_b=team_b,
                winner_team=team_a, status="finished",
            )
        for _ in range(2):
            Match.objects.create(
                tournament=t2, team_a=team_a, team_b=team_b,
                winner_team=team_b, status="finished",
            )

        with connection.cursor() as cur:
            cur.execute(self.ALL_TIME_SQL)
            rows = cur.fetchall()

        names = [r[0] for r in rows]
        counts = [r[1] for r in rows]
        assert "sql_team_a" in names
        a_count = dict(rows)["sql_team_a"]
        b_count = dict(rows)["sql_team_b"]
        assert a_count == 3
        assert b_count == 2
        assert counts == sorted(counts, reverse=True)

    def test_per_tournament_excludes_other_tournaments(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        t2 = Tournament.objects.create(
            name="sql_t3",
            format="single_elim",
            max_teams=4,
            start_date=datetime.date(2025, 3, 1),
            end_date=datetime.date(2025, 3, 31),
        )
        # 2 wins for team_a in tournament 1
        for _ in range(2):
            Match.objects.create(
                tournament=tournament, team_a=team_a, team_b=team_b,
                winner_team=team_a, status="finished",
            )
        # 4 wins for team_a in tournament 2 — must NOT appear in t1 filter
        for _ in range(4):
            Match.objects.create(
                tournament=t2, team_a=team_a, team_b=team_b,
                winner_team=team_a, status="finished",
            )

        with connection.cursor() as cur:
            cur.execute(self.PER_TOURNAMENT_SQL, [tournament.id])
            rows = dict(cur.fetchall())

        assert rows.get("sql_team_a") == 2, f"Expected 2, got {rows}"
        assert "sql_team_b" not in rows

    def test_team_with_zero_wins_excluded(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b,
            winner_team=team_a, status="finished",
        )

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
    """JOIN teams twice with aliases team_a / team_b."""

    SQL = """
        SELECT m.id          AS match_id,
               ta.name       AS team_a_name,
               tb.name       AS team_b_name,
               m.winner_team_id,
               m.played_at
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

    def test_returns_pending_and_finished_matches(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        pending = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b, status="pending"
        )
        finished = Match.objects.create(
            tournament=tournament, team_a=team_a, team_b=team_b,
            winner_team=team_a, status="finished",
        )

        with connection.cursor() as cur:
            cur.execute(self.SQL)
            ids = {r[0] for r in cur.fetchall()}

        assert pending.id in ids
        assert finished.id in ids

    def test_result_columns_present(self, db, match):
        with connection.cursor() as cur:
            cur.execute(self.SQL + " WHERE m.id = %s", [match.id])
            description = [d[0] for d in cur.description]

        assert description == ["match_id", "team_a_name", "team_b_name", "winner_team_id", "played_at"]


# ---------------------------------------------------------------------------
# 5. Transactional ELO recalculation
# ---------------------------------------------------------------------------


def _elo_new(my_elo: int, opp_elo: int, won: bool) -> int:
    """Python reference implementation of the Elo K=32 formula."""
    expected = 1.0 / (1 + 10 ** ((opp_elo - my_elo) / 400.0))
    result = 1 if won else 0
    return round(my_elo + 32 * (result - expected))


def _run_elo_transaction(match_id, winner_team_id, winner_user_id, loser_user_id,
                         winner_elo, loser_elo):
    """Execute the ELO recalculation transaction block."""
    new_winner_elo = _elo_new(winner_elo, loser_elo, won=True)
    new_loser_elo = _elo_new(loser_elo, winner_elo, won=False)

    with connection.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute(
                "UPDATE matches SET winner_team_id = %s WHERE id = %s",
                [winner_team_id, match_id],
            )
            cur.execute(
                "UPDATE users SET elo = %s WHERE id = %s",
                [new_winner_elo, winner_user_id],
            )
            cur.execute(
                "UPDATE users SET elo = %s WHERE id = %s",
                [new_loser_elo, loser_user_id],
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise


@pytest.mark.integration
@pytest.mark.django_db
class EloTransactionTest:
    """Transaction updates winner_team_id and both users' ELOs atomically."""

    def test_winner_elo_increases(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams

        _run_elo_transaction(
            match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo
        )

        winner.refresh_from_db()
        assert winner.elo > 1200

    def test_loser_elo_decreases(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams

        _run_elo_transaction(
            match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo
        )

        loser.refresh_from_db()
        assert loser.elo < 1000

    def test_winner_team_id_set(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams

        _run_elo_transaction(
            match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo
        )

        match.refresh_from_db()
        assert match.winner_team_id == team_a.id

    def test_elo_values_are_integers(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams

        _run_elo_transaction(
            match.id, team_a.id, winner.id, loser.id, winner.elo, loser.elo
        )

        with connection.cursor() as cur:
            cur.execute("SELECT elo FROM users WHERE id = %s", [winner.id])
            elo_val = cur.fetchone()[0]

        assert isinstance(elo_val, int)

    def test_rollback_leaves_rows_unchanged(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        original_winner_elo = winner.elo
        original_loser_elo = loser.elo

        # Force an error by passing a non-existent user_id on the second UPDATE
        with pytest.raises(Exception):
            with connection.cursor() as cur:
                cur.execute("BEGIN")
                try:
                    cur.execute(
                        "UPDATE matches SET winner_team_id = %s WHERE id = %s",
                        [team_a.id, match.id],
                    )
                    cur.execute(
                        "UPDATE users SET elo = %s WHERE id = %s",
                        [9999, winner.id],
                    )
                    # Force failure: divide-by-zero via SQL error
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


# ---------------------------------------------------------------------------
# 6. Per-team match history
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class TeamHistoryQueryTest:
    """Chronological match history for a given team with win/loss result."""

    SQL = """
        SELECT m.id AS match_id,
               m.played_at,
               CASE
                   WHEN m.team_a_id = %(team_id)s THEN tb.name
                   ELSE ta.name
               END AS opponent,
               CASE
                   WHEN m.winner_team_id = %(team_id)s THEN 'win'
                   ELSE 'loss'
               END AS result
        FROM matches m
        JOIN teams ta ON m.team_a_id = ta.id
        JOIN teams tb ON m.team_b_id = tb.id
        WHERE m.team_a_id = %(team_id)s
           OR m.team_b_id = %(team_id)s
        ORDER BY m.played_at ASC
    """

    def _make_match(self, tournament, team_a, team_b, winner, played_at):
        return Match.objects.create(
            tournament=tournament,
            team_a=team_a,
            team_b=team_b,
            winner_team=winner,
            status="finished",
            played_at=played_at,
        )

    def test_history_ordered_by_date_ascending(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        self._make_match(tournament, team_a, team_b, team_b, datetime.datetime(2025, 3, 1, tzinfo=datetime.timezone.utc))
        self._make_match(tournament, team_a, team_b, team_a, datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))
        self._make_match(tournament, team_a, team_b, team_a, datetime.datetime(2025, 2, 1, tzinfo=datetime.timezone.utc))

        with connection.cursor() as cur:
            cur.execute(self.SQL, {"team_id": team_a.id})
            rows = cur.fetchall()

        dates = [r[1] for r in rows]
        assert dates == sorted(dates)

    def test_result_column_win_and_loss(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        self._make_match(tournament, team_a, team_b, team_a, datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))
        self._make_match(tournament, team_a, team_b, team_b, datetime.datetime(2025, 2, 1, tzinfo=datetime.timezone.utc))

        with connection.cursor() as cur:
            cur.execute(self.SQL, {"team_id": team_a.id})
            results = [r[3] for r in cur.fetchall()]

        assert results == ["win", "loss"]

    def test_opponent_resolved_when_team_is_team_a(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        self._make_match(tournament, team_a, team_b, team_a, datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))

        with connection.cursor() as cur:
            cur.execute(self.SQL, {"team_id": team_a.id})
            row = cur.fetchone()

        assert row[2] == "sql_team_b"

    def test_opponent_resolved_when_team_is_team_b(self, db, two_teams, tournament):
        team_a, team_b = two_teams
        self._make_match(tournament, team_a, team_b, team_b, datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))

        with connection.cursor() as cur:
            cur.execute(self.SQL, {"team_id": team_b.id})
            row = cur.fetchone()

        assert row[2] == "sql_team_a"


# ---------------------------------------------------------------------------
# 7. ELO atomicity — match-tracking spec consistency
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.django_db
class EloAtomicityTest:
    """Partial failure in the ELO block must leave both winner_team_id and elo unchanged."""

    def test_partial_failure_leaves_all_unchanged(self, db, match, two_players, two_teams):
        winner, loser = two_players
        team_a, _ = two_teams
        original_winner_elo = winner.elo
        original_loser_elo = loser.elo

        with pytest.raises(Exception):
            with connection.cursor() as cur:
                cur.execute("BEGIN")
                try:
                    cur.execute(
                        "UPDATE matches SET winner_team_id = %s WHERE id = %s",
                        [team_a.id, match.id],
                    )
                    cur.execute(
                        "UPDATE users SET elo = %s WHERE id = %s",
                        [_elo_new(winner.elo, loser.elo, True), winner.id],
                    )
                    # Simulate second user UPDATE failing
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
