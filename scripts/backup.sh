#!/usr/bin/env bash
# PostgreSQL backup script for production cron
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-shopbot}"
PGDATABASE="${PGDATABASE:-shopbot}"

export PGPASSWORD="${PGPASSWORD:-shopbot}"

pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -Fc "$PGDATABASE" \
  > "$BACKUP_DIR/shopbot_${TIMESTAMP}.dump"

echo "Backup saved to $BACKUP_DIR/shopbot_${TIMESTAMP}.dump"

# Keep last 7 days
find "$BACKUP_DIR" -name "shopbot_*.dump" -mtime +7 -delete
