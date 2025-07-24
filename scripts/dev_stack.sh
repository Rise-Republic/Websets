#!/bin/bash
# Start the full local development stack with one command
set -e

# Ensure dependencies are installed
make setup

# Generate mTLS certs if missing
if [ ! -d certs ] || [ -z "$(ls certs/*.crt 2>/dev/null)" ]; then
    echo "Generating mTLS certificates..."
    scripts/generate_mtls_certs.sh
fi

# Build and start all services
echo "Starting services with Docker Compose..."
docker compose up -d --build

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
seed_cmd="from app.database import SessionLocal; from app.models import User; from app.auth.jwt_handler import get_password_hash; db=SessionLocal();\nif not db.query(User).first():\n    user=User(email='admin@example.com', hashed_password=get_password_hash('admin'));\n    db.add(user); db.commit(); print('Created default user admin@example.com / admin');\ndb.close()"
docker compose exec -T app python - <<PY
$seed_cmd
PY

echo "Local development stack is running."

