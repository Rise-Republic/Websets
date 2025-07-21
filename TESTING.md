# Testing Guide

This project includes comprehensive test suites for both backend and frontend components.

## Backend Testing (Python)

### Prerequisites
- Python 3.11+
- PostgreSQL (for integration tests)
- Redis (for integration tests)

### Test Structure
- `tests/unit/` - Unit tests for business logic
- `tests/integration/` - Integration tests for API endpoints
- `tests/conftest.py` - Shared test fixtures and configuration

### Running Backend Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test categories
python -m pytest -m unit
python -m pytest -m integration

# Run specific test file
python -m pytest tests/unit/test_auth.py

# Run with verbose output
python -m pytest -v
```

### Test Configuration
- `pytest.ini` - Main pytest configuration
- Test database: SQLite in-memory for unit tests
- External services are mocked using `pytest-mock`

## Frontend Testing (React/TypeScript)

### Prerequisites
- Node.js 18+
- npm

### Test Structure
- `src/**/*.test.tsx` - Component tests
- `src/**/*.test.ts` - Hook and utility tests
- `src/__tests__/utils/` - Test utilities and helpers

### Running Frontend Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- LoginForm.test.tsx
```

### Test Configuration
- `jest.config.js` - Jest configuration
- `src/setupTests.ts` - Global test setup
- Coverage thresholds: 70% for all metrics

## Coverage Targets

### Backend
- **Target**: 80% coverage
- **Location**: `htmlcov/index.html` (after running with `--cov-report=html`)

### Frontend  
- **Target**: 70% coverage
- **Location**: `coverage/lcov-report/index.html` (after running `npm run test:coverage`)

## Mocking Strategy

### Backend
- **External APIs**: OpenAI, Anthropic, HTTP clients
- **Databases**: SQLite in-memory for unit tests
- **Services**: Redis, Celery for integration tests

### Frontend
- **API calls**: Mocked using Jest mocks
- **Hooks**: Custom render utilities with context providers
- **Browser APIs**: localStorage, sessionStorage, fetch

## Continuous Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`

CI includes:
- Backend unit and integration tests
- Frontend unit tests  
- Coverage reporting
- Build verification

## Writing New Tests

### Backend Tests
1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Use appropriate markers: `@pytest.mark.unit` or `@pytest.mark.integration`
4. Mock external dependencies
5. Follow AAA pattern (Arrange, Act, Assert)

### Frontend Tests
1. Co-locate tests with components (`ComponentName.test.tsx`)
2. Use React Testing Library best practices
3. Test user interactions, not implementation details
4. Use custom render utilities for components requiring context

## Troubleshooting

### Common Issues

#### Backend
- **Import errors**: Ensure `PYTHONPATH` includes project root
- **Database errors**: Check PostgreSQL connection for integration tests  
- **Mock issues**: Verify mock patches target correct modules

#### Frontend
- **Transform errors**: Check Jest configuration for TypeScript files
- **Module resolution**: Verify path mapping in `jest.config.js`
- **Context errors**: Use `renderWithProviders` for components using hooks

### Performance Tips
- Use `pytest-xdist` for parallel test execution
- Focus tests with `pytest -k "pattern"`
- Skip slow tests in development with `pytest -m "not slow"`