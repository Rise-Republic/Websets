#!/bin/bash
# Dump the PostgreSQL database for backup
set -euo pipefail

DB_CONTAINER=${DB_CONTAINER:-websets-db-1}
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-webset_miner}
BACKUP_FILE=${1:-backup.sql}

# Perform the dump from the running container
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

echo "Database dump saved to $BACKUP_FILE"
