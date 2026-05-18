-- ELO Recalculation Transaction Block
-- =====================================
-- Paste this entire file into psql, or run with:
--     psql $DATABASE_URL -f scripts/elo_transaction.sql
--
-- Set variables before running (replace with real values):
\set match_id         1
\set winner_team_id   1
\set winner_user_id   1
\set loser_user_id    2
\set winner_old_elo   1200
\set loser_old_elo    1000
--
-- The Elo formula (K=32):
--   expected = 1 / (1 + 10^((opponent_elo - player_elo) / 400))
--   new_elo  = ROUND(old_elo + 32 * (actual_result - expected))
-- where actual_result = 1 for winner, 0 for loser.

BEGIN;

-- Step 1: record the winner
UPDATE matches
SET winner_team_id = :winner_team_id
WHERE id = :match_id;

-- Step 2: update winner ELO (+)
UPDATE users
SET elo = ROUND(
    (:winner_old_elo + 32.0 * (
        1 - 1.0 / (1 + POWER(10, (:loser_old_elo - :winner_old_elo) / 400.0))
    ))::NUMERIC
)::INTEGER
WHERE id = :winner_user_id;

-- Step 3: update loser ELO (-)
UPDATE users
SET elo = ROUND(
    (:loser_old_elo + 32.0 * (
        0 - 1.0 / (1 + POWER(10, (:winner_old_elo - :loser_old_elo) / 400.0))
    ))::NUMERIC
)::INTEGER
WHERE id = :loser_user_id;

COMMIT;

-- If any step above fails, run ROLLBACK instead of COMMIT:
-- ROLLBACK;
--
-- To verify results after commit:
-- SELECT id, username, elo FROM users WHERE id IN (:winner_user_id, :loser_user_id);
-- SELECT id, winner_team_id FROM matches WHERE id = :match_id;
