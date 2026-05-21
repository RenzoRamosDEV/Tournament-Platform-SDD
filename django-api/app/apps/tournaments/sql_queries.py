"""
Canonical raw SQL queries for the tournament platform.

These are validated in psql before use in Django ORM. Run each query with
EXPLAIN ANALYZE in psql to confirm index usage and query plan.
"""

from django.db import connection


# ---------------------------------------------------------------------------
# 1. Leaderboard — top 50 users by ELO (uses users_elo_desc_idx)
# ---------------------------------------------------------------------------

LEADERBOARD_SQL = """
SELECT username, elo
FROM users
ORDER BY elo DESC
LIMIT 50
"""


def get_leaderboard(limit: int = 50) -> list[tuple]:
    """Return (username, elo) tuples for the top `limit` players."""
    sql = "SELECT username, elo FROM users ORDER BY elo DESC LIMIT %s"
    with connection.cursor() as cur:
        cur.execute(sql, [limit])
        return cur.fetchall()


# ---------------------------------------------------------------------------
# 2. Team wins — all-time
# ---------------------------------------------------------------------------

TEAM_WINS_ALL_TIME_SQL = """
SELECT t.name  AS team_name,
       COUNT(m.id) AS win_count
FROM teams t
JOIN matches m ON m.winner_team_id = t.id
GROUP BY t.id, t.name
ORDER BY win_count DESC
"""


def get_team_wins_all_time() -> list[tuple]:
    """Return (team_name, win_count) ordered by win_count DESC for all tournaments."""
    with connection.cursor() as cur:
        cur.execute(TEAM_WINS_ALL_TIME_SQL)
        return cur.fetchall()


# ---------------------------------------------------------------------------
# 3. Team wins — per tournament
# ---------------------------------------------------------------------------

TEAM_WINS_PER_TOURNAMENT_SQL = """
SELECT t.name  AS team_name,
       COUNT(m.id) AS win_count
FROM teams t
JOIN matches m ON m.winner_team_id = t.id
WHERE m.tournament_id = %s
GROUP BY t.id, t.name
ORDER BY win_count DESC
"""


def get_team_wins_per_tournament(tournament_id: int) -> list[tuple]:
    """Return (team_name, win_count) scoped to a single tournament."""
    with connection.cursor() as cur:
        cur.execute(TEAM_WINS_PER_TOURNAMENT_SQL, [tournament_id])
        return cur.fetchall()


# ---------------------------------------------------------------------------
# 4. All matches with both team names resolved (dual alias JOIN)
# ---------------------------------------------------------------------------

MATCHES_WITH_TEAMS_SQL = """
SELECT m.id          AS match_id,
       ta.name       AS team_a_name,
       tb.name       AS team_b_name,
       m.winner_team_id,
       m.played_at
FROM matches m
JOIN teams ta ON m.team_a_id = ta.id
JOIN teams tb ON m.team_b_id = tb.id
"""


def get_matches_with_teams() -> list[tuple]:
    """Return all matches with team names resolved via aliased JOINs."""
    with connection.cursor() as cur:
        cur.execute(MATCHES_WITH_TEAMS_SQL)
        return cur.fetchall()


# ---------------------------------------------------------------------------
# 5. ELO recalculation — Python helper + transaction executor
# ---------------------------------------------------------------------------

def _elo_new(my_elo: int, opp_elo: int, won: bool) -> int:
    """Standard Elo formula with K=32, rounded to nearest integer."""
    expected = 1.0 / (1 + 10 ** ((opp_elo - my_elo) / 400.0))
    return round(my_elo + 32 * ((1 if won else 0) - expected))


def record_match_result(
    match_id: int,
    winner_team_id: int,
    winner_user_id: int,
    loser_user_id: int,
    winner_elo: int,
    loser_elo: int,
) -> None:
    """
    Record a match result and recalculate ELO for both users atomically.

    Updates matches.winner_team_id and both users' elo in a single transaction.
    Rolls back all changes if any statement fails.
    """
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


# ---------------------------------------------------------------------------
# 6. Per-team match history — chronological with win/loss result
# ---------------------------------------------------------------------------

TEAM_HISTORY_SQL = """
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


def get_team_history(team_id: int) -> list[tuple]:
    """Return (match_id, played_at, opponent, result) for all matches involving team_id."""
    with connection.cursor() as cur:
        cur.execute(TEAM_HISTORY_SQL, {"team_id": team_id})
        return cur.fetchall()
