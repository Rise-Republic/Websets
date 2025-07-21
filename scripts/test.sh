#!/bin/bash

# Backend tests
echo "Running backend tests..."
cd "$(dirname "$0")/.."
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:backend-coverage

# Frontend tests
echo "Running frontend tests..."
npm run test:coverage

# Generate combined test report
echo "Test execution completed!"
echo "Backend coverage: ./backend-coverage/index.html"
echo "Frontend coverage: ./coverage/lcov-report/index.html"