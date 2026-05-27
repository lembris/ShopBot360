#!/bin/bash
# Runs once when the Postgres data volume is first created.
# Official image already created POSTGRES_USER and POSTGRES_DB from env vars.
set -euo pipefail

echo "[shopbot-init] Initializing database: ${POSTGRES_DB} for user: ${POSTGRES_USER}"

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<EOSQL
-- Extensions required by ShopBot (UUID generation, etc.)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Session defaults for the shop bot app
ALTER DATABASE "${POSTGRES_DB}" SET timezone TO 'Africa/Dar_es_Salaam';

-- Ensure application user owns the public schema and has full access
GRANT ALL PRIVILEGES ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_USER}";
GRANT ALL ON SCHEMA public TO "${POSTGRES_USER}";
ALTER SCHEMA public OWNER TO "${POSTGRES_USER}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${POSTGRES_USER}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${POSTGRES_USER}";

-- Marker table so we can verify init ran (optional diagnostics)
CREATE TABLE IF NOT EXISTS _shopbot_init (
    id SERIAL PRIMARY KEY,
    initialized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    app_version TEXT NOT NULL DEFAULT '1.0.0'
);
INSERT INTO _shopbot_init (app_version) VALUES ('1.0.0');
EOSQL

echo "[shopbot-init] Database ${POSTGRES_DB} ready (extensions + grants applied)."
