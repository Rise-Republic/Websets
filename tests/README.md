# Test Suite Structure

This directory contains multiple test suites organized by scope:

- **unit/** – Fast tests for individual functions and classes. These use the `@pytest.mark.unit` marker.
- **integration/** – Tests that hit the API and database. They use the `@pytest.mark.integration` marker and may require services such as PostgreSQL or Redis running locally.
- **performance/** – Benchmarks and stress tests. They are marked `@pytest.mark.slow` and are skipped in regular CI runs.
- **e2e/** – End-to-end tests that start the application with Uvicorn. These use the `@pytest.mark.e2e` marker.

Additional test categories include `contract/` which holds API contract checks marked with `@pytest.mark.contract`.

## Running Tests

Use pytest markers to run specific suites:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance tests
pytest -m slow

# End-to-end tests
pytest -m e2e
```

## Artifacts

Coverage reports are written to `htmlcov/` when tests are run with `--cov-report=html` (enabled by default via `pytest.ini`). Open `htmlcov/index.html` after a run to view results.

### Quick Start

Install the development requirements and run a minimal test suite:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --maxfail=1 --disable-warnings -q
```

Generate a coverage summary:

```bash
pytest --cov=app --cov-report=term-missing
```

