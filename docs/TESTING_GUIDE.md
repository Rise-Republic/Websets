# Testing Guide

This project includes unit, integration and end‑to‑end tests for both the backend and frontend. CI runs the same commands via `scripts/ci-run.sh`.

## Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
npm ci

# Backend
pytest

# Frontend
npm test
```

Use markers to run a subset:

```bash
pytest -m unit        # only unit tests
pytest -m integration # integration tests
npm test -- LoginForm.test.tsx # single frontend test
```

Coverage reports are generated in `htmlcov/` for Python and `coverage/lcov-report/` for the frontend. Target coverage is **80%** for both.

## Continuous Integration

CI executes `scripts/ci-run.sh` which builds the Docker stack, waits for health checks, runs linters and then executes the test suites. To run the same checks locally:

```bash
bash scripts/ci-run.sh
```

## Self‑Healing Tests

Tests are organized to be idempotent and clean up resources. If a test fails intermittently, add retry logic using `pytest-rerunfailures` and open an issue for investigation.

