CREATE TABLE IF NOT EXISTS users (
    id         UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    username   VARCHAR(255) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       VARCHAR(20)  NOT NULL,
    elo        INTEGER      NOT NULL DEFAULT 1000,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP    NOT NULL DEFAULT now(),
    is_active  BOOLEAN      NOT NULL DEFAULT true,
    is_staff   BOOLEAN      NOT NULL DEFAULT false,
    last_login TIMESTAMP
);
