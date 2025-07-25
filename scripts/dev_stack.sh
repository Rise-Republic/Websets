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
docker compose exec -T app bash -c 'DB_URL="postgresql://postgres:changeme@db:5432/webset_miner" alembic upgrade head'

# Seed default user if none exists
# Set default values if not provided
SEED_USER_EMAIL=${SEED_USER_EMAIL:-admin@example.com}
SEED_USER_PASSWORD=${SEED_USER_PASSWORD:-admin}

echo "Seeding default user: $SEED_USER_EMAIL"

# Explicitly set the correct DATABASE_URL for the Docker environment
docker compose exec -T \
  -e SEED_USER_EMAIL="$SEED_USER_EMAIL" \
  -e SEED_USER_PASSWORD="$SEED_USER_PASSWORD" \
  -e DATABASE_URL="postgresql://postgres:changeme@db:5432/webset_miner" \
  app python scripts/seed_default_user.py

echo "Local development stack is running."

