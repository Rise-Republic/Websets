# Testing Strategy

This Architectural Decision Record (ADR) describes the layered testing approach for the Websets project. It captures tooling, quality thresholds, and ownership for each layer.

## Test Layers

### Unit
- **Purpose:** Validate individual functions and components in isolation.
- **Tooling:** `pytest` with `coverage.py` for the backend; `jest` for the frontend.
- **Thresholds:** ≥80% line coverage and ≥70% mutation score using `mutmut` (Python) and `stryker` (JavaScript).

### Integration
- **Purpose:** Verify behavior against real databases or external services.
- **Tooling:** `pytest -m integration` executed against Docker‑managed dependencies.
- **Thresholds:** Contributes to global coverage goals; mutation testing is optional.

### Contract
- **Purpose:** Ensure API compatibility between consumers and providers.
- **Tooling:** `pact` for consumer/provider contract verification.
- **Thresholds:** Pact verification must pass for all interactions; coverage not tracked.

### End-to-End
- **Purpose:** Exercise complete user workflows through the UI and API.
- **Tooling:** `Playwright` executed via `npm run system`.
- **Thresholds:** All critical user journeys must succeed; coverage metrics are not enforced.

### Performance
- **Purpose:** Measure throughput and latency under expected load.
- **Tooling:** `Locust` scenarios in `tests/performance`.
- **Thresholds:** 95th percentile response time <500 ms with <1% error rate.

### Security
- **Purpose:** Detect vulnerabilities in code and runtime configuration.
- **Tooling:** `OWASP ZAP`, `gitleaks`, and dependency vulnerability scanners.
- **Thresholds:** No outstanding high‑severity findings.

## Coverage and Mutation Targets

- **Backend:** 80% line coverage, 70% mutation score.
- **Frontend:** 80% line coverage, 70% mutation score.

Coverage reports are produced by `pytest --cov` and `npm test -- --coverage`. Mutation testing uses `mutmut run` and `npx stryker run`.

## Ownership Map

| Layer                      | Owner         |
| -------------------------- | ------------- |
| Backend unit tests         | Backend Team  |
| Frontend unit tests        | Frontend Team |
| Integration & contract     | Platform Team |
| End-to-end                 | QA Team       |
| Performance                | SRE Team      |
| Security                   | Security Team |

Each team maintains tooling for their layer and is responsible for meeting the defined thresholds in CI.
