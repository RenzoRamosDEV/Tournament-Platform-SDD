-- Creates a separate database for the auth-service so it does not
-- conflict with the Django schema (different user ID types: UUID vs bigint).
SELECT 'CREATE DATABASE auth_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec
