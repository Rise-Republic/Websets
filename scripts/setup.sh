#!/bin/bash
set -e

# WebSet Miner setup script

echo "Setting up WebSet Miner..."

# Create data directories
mkdir -p data/crawled
mkdir -p data/screenshots  
mkdir -p data/vector_store

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please update with your API keys"
fi

# Install Python dependencies
echo "Installing Python dependencies..."

# Create Python virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Use pip from the virtual environment
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -r requirements-dev.txt

# Install Node dependencies if package.json exists
if [ -f frontend/package.json ]; then
    echo "Installing Node dependencies..."
    (cd frontend && bash -c "npm ci")
fi

# Install Playwright browsers if missing
PLAYWRIGHT_DIR="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
if [ ! -d "$PLAYWRIGHT_DIR/chromium" ]; then
    echo "Installing Playwright browsers..."
    ./.venv/bin/playwright install chromium
fi

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Start services: docker compose up -d"
echo "3. Run a test job: python scripts/run_job.py 'AI startups in Silicon Valley'"