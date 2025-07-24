#!/bin/bash
# Start the full local development stack with one command
set -euo pipefail

# Ensure dependencies are installed
make setup

# Export variables from .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Configure local database URL if unset
DB_PASSWORD=$(cat ./secrets/postgres_password)
DEFAULT_DB_URL="postgresql://postgres:${DB_PASSWORD}@db:5432/webset_miner"
if [ -z "${DATABASE_URL:-}" ]; then
  DATABASE_URL="$DEFAULT_DB_URL"
  echo "DATABASE_URL=$DATABASE_URL" >> .env
fi
export DATABASE_URL

# Disable Vault for local development unless explicitly set
if [ -z "${DISABLE_VAULT:-}" ]; then
  DISABLE_VAULT=true
  echo "DISABLE_VAULT=true" >> .env
fi
export DISABLE_VAULT

# Generate mTLS certs if missing
if [ ! -d certs ] || [ -z "$(ls certs/*.crt 2>/dev/null)" ]; then
    echo "Generating mTLS certificates..."
    scripts/generate_mtls_certs.sh
fi

# Build and start all services
echo "Starting services with Docker Compose..."
docker compose up -d --build

# Seed Vault with template secrets
scripts/seed_vault.sh

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

seed_cmd="from app.database import SessionLocal; from app.models import User; from app.auth.jwt_handler import get_password_hash; import os; db=SessionLocal();\nemail=os.environ['SEED_USER_EMAIL']; password=os.environ['SEED_USER_PASSWORD'];\nif not db.query(User).first():\n    user=User(email=email, hashed_password=get_password_hash(password));\n    db.add(user); db.commit(); print(f'Created default user {email}');\ndb.close()"
docker compose exec -T -e SEED_USER_EMAIL -e SEED_USER_PASSWORD app python - <<PY
$seed_cmd
PY

echo "Local development stack is running."

