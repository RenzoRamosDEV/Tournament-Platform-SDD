#!/bin/sh
set -e

# Check psql version >= 15
check_version() {
    version_output=$(psql --version 2>&1)
    major=$(echo "$version_output" | grep -oE '[0-9]+\.[0-9]+' | head -1 | cut -d. -f1)
    if [ -z "$major" ] || [ "$major" -lt 15 ]; then
        echo "Error: PostgreSQL >= 15 is required. Found: $version_output" >&2
        exit 1
    fi
}

check_version

if [ "$1" = "--check-version-only" ]; then
    exit 0
fi

: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
DB_NAME="${DB_NAME:-tournament_platform}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"

psql -U postgres <<SQL
CREATE ROLE IF NOT EXISTS ${DB_USER} LOGIN CREATEDB PASSWORD '${DB_PASSWORD}';
SQL

psql -U postgres <<SQL
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
SQL

python app/manage.py migrate
