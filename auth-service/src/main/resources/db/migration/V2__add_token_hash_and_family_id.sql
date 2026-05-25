ALTER TABLE refresh_tokens
    DROP COLUMN IF EXISTS token;

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS token_hash  VARCHAR(64)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS family_id   UUID         NOT NULL DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS created_at  TIMESTAMP    NOT NULL DEFAULT now();

ALTER TABLE refresh_tokens
    ADD CONSTRAINT uq_refresh_tokens_token_hash UNIQUE (token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family_id  ON refresh_tokens (family_id);

ALTER TABLE refresh_tokens ALTER COLUMN token_hash DROP DEFAULT;
ALTER TABLE refresh_tokens ALTER COLUMN family_id  DROP DEFAULT;
