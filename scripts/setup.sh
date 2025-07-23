#!/bin/bash

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
pip install -r requirements.txt -r requirements-dev.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Start services: docker compose up -d"
echo "3. Run a test job: python scripts/run_job.py 'AI startups in Silicon Valley'"