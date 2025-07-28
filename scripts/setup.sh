#!/bin/bash
set -e

# WebSet Miner setup script
# Run as a regular user; sudo is not required.

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

# Ensure a clean virtual environment without sudo
if [ -d ".venv" ]; then
    echo "Removing existing .venv directory..."
    rm -rf .venv
fi

echo "Creating Python virtual environment..."
python3 -m venv .venv

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
    # Try to install system dependencies first, then browsers
    if ./.venv/bin/playwright install-deps chromium 2>/dev/null; then
        echo "Playwright system dependencies installed successfully"
    else
        echo "Warning: Could not install Playwright system dependencies (may require sudo)"
    fi
    
    # Install Playwright browsers with error handling
    if ./.venv/bin/playwright install chromium; then
        echo "Playwright browsers installed successfully"
    else
        echo "Warning: Playwright browser installation failed. You may need to install manually or use a different browser."
        echo "Alternative: You can use Firefox with: playwright install firefox"
    fi
fi

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Start services: docker compose up -d"
echo "3. Run a test job: python scripts/run_job.py 'AI startups in Silicon Valley'"
