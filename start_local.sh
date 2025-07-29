#!/bin/bash
# Simple startup script for local development
set -e

echo "🚀 Starting Websets locally..."

# Set environment variables
export DATABASE_URL="sqlite:///./data/websets_local.db"
export OPENAI_API_KEY="sk-dev-openai-key-for-local-development-only-0123456789"
export REDIS_URL="redis://localhost:6379"
export CELERY_BROKER_URL="redis://localhost:6379"
export CELERY_RESULT_BACKEND="redis://localhost:6379"
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"

# WorkOS Configuration (test credentials)
export WORKOS_API_KEY_TEST="sk_test_a2V5XzAxSkU0VEtXSFZNWjVSMVc5WU0wVlkyNk5OLHZvaHZmQ0oxQ3FSamcxS3g4YVIyMHJrblk"
export WORKOS_CLIENT_ID_TEST="client_01JE4TKWHVMZ5R1W9YM0VY26NN"
export WORKOS_API_KEY="sk_test_a2V5XzAxSkU0VEtXSFZNWjVSMVc5WU0wVlkyNk5OLHZvaHZmQ0oxQ3FSamcxS3g4YVIyMHJrblk"
export WORKOS_CLIENT_ID="client_01JE4TKWHVMZ5R1W9YM0VY26NN"

# Additional settings
export DATA_DIR="./data"
export VECTOR_STORE_PATH="./data/vector_store"
export MAX_CONCURRENT_CRAWLS="3"
export REQUEST_DELAY_MS="1000"
export USER_AGENT="WebSetMiner/1.0-local"

# Create data directory
mkdir -p data

# Check if Redis is running
if ! redis-cli ping >/dev/null 2>&1; then
    echo "🔄 Starting Redis..."
    sudo service redis-server start
fi

echo "✅ Redis is running"

# Start the FastAPI application
echo "🌟 Starting Websets application on http://localhost:8001"
echo "📝 Note: Database tables will be created automatically on first run"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
