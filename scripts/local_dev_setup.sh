#!/bin/bash
# Local development setup script for Websets (without Docker)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "🚀 Setting up Websets for local development (without Docker)..."

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/vector_store
mkdir -p data/uploads
mkdir -p data/logs

# Set up environment variables for local development
echo "⚙️  Setting up environment variables..."
cat > .env.local << EOF
# Local development environment (without Docker)
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://postgres:changeme@localhost:5432/webset_miner

# Redis Configuration
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Local paths
DATA_DIR=./data
VECTOR_STORE_PATH=./data/vector_store

# API Keys (for development)
OPENAI_API_KEY=sk-dev-openai-key-for-local-development-only-0123456789

# WorkOS Configuration (test keys)
WORKOS_API_KEY_TEST=sk_test_a2V5XzAxSkU0VEtXSFZNWjVSMVc5WU0wVlkyNk5OLHZvaHZmQ0oxQ3FSamcxS3g4YVIyMHJrblk
WORKOS_CLIENT_ID_TEST=client_01JE4TKWHVMZ5R1W9YM0VY26NN

# Local development settings
MAX_CONCURRENT_CRAWLS=3
REQUEST_DELAY_MS=1000
USER_AGENT=WebSetMiner/1.0-local

# Seed user for development
SEED_USER_EMAIL=admin@example.com
SEED_USER_PASSWORD=admin
WEBSETS_TEST_USER_PASSWORD=testpassword123

# Disable services that require complex setup
VAULT_ADDR=
MINIO_ENDPOINT=
QDRANT_URL=
WEAVIATE_URL=
EOF

echo "✅ Environment configuration created at .env.local"

# Check if PostgreSQL is installed and running
if command -v psql >/dev/null 2>&1; then
    echo "✅ PostgreSQL is available"
else
    echo "❌ PostgreSQL not found. Installing..."
    sudo apt update && sudo apt install -y postgresql postgresql-contrib
fi

# Check if Redis is running
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "🔄 Starting Redis..."
    sudo service redis-server start
fi

echo ""
echo "🎉 Local development setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up PostgreSQL database:"
echo "   sudo -u postgres createuser -s $(whoami)"
echo "   createdb webset_miner"
echo ""
echo "2. Run database migrations:"
echo "   python -m alembic upgrade head"
echo ""
echo "3. Start the application:"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "4. Access the application at: http://localhost:8001"
echo ""
