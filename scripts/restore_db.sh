#!/bin/bash
# Restore a PostgreSQL dump into the database container and validate application health
set -euo pipefail

DB_CONTAINER=${DB_CONTAINER:-websets-db-1}
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-webset_miner}
BACKUP_FILE=${1:-backup.sql}
APP_HEALTH_URL=${APP_HEALTH_URL:-http://localhost:8001/v1/health}

# Wait for the database to become ready
for i in {1..30}; do
  if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    break
  fi
  echo "Waiting for database..."
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo "Database is not ready" >&2
    exit 1
  fi
done

# Restore the dump into the running container
echo "Restoring database from $BACKUP_FILE..."
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

echo "Database restored. Verifying application health..."

# Poll application health endpoint
for i in {1..30}; do
  if curl -fsS "$APP_HEALTH_URL" >/dev/null 2>&1; then
    echo "Application healthy at $APP_HEALTH_URL"
    exit 0
  fi
  echo "Waiting for application health..."
  sleep 5
done

echo "Application health check failed" >&2
exit 1
