#!/bin/bash
# Start the full local development stack with one command
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Ensure dependencies are installed
make setup

# Generate mTLS certs if missing
if [ ! -d certs ] || [ -z "$(ls certs/*.crt 2>/dev/null)" ]; then
    echo "Generating mTLS certificates..."
    python scripts/generate_mtls_certs.py
fi

# Build and start all services
echo "Starting services with Docker Compose..."
docker compose up -d --build

# Seed Vault with template secrets
"$SCRIPT_DIR/seed_vault.sh"

# Wait for database to be ready
until docker compose exec -T db pg_isready -U postgres >/dev/null 2>&1; do
  echo "Waiting for database..."
  sleep 2
done

# Apply database migrations
echo "Applying database migrations..."
# Pass database URL for Alembic via DB_URL
docker compose exec -T app bash -c 'DB_URL="$DATABASE_URL" alembic upgrade head'

# Seed default user if none exists
if [ -z "${SEED_USER_EMAIL}" ] || [ -z "${SEED_USER_PASSWORD}" ]; then
  echo "SEED_USER_EMAIL and SEED_USER_PASSWORD must be set to seed the initial user." >&2
  exit 1
fi

docker compose exec -T \
  -e SEED_USER_EMAIL -e SEED_USER_PASSWORD \
  app python scripts/seed_default_user.py

echo "Local development stack is running."

