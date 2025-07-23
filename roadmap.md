# WebSet Miner: Roadmap & Prioritized Actions

## Roadmap Overview

This roadmap is broken down into Sprints, Epics, and Tasks. Each task is mapped to a priority (P0–P3), estimated effort (S/M/L), and owner role. All improvements from the audit are included.

---

## Sprint/Epic/Task Structure

- **Sprint:** 2 weeks
- **Epic:** Thematic grouping (e.g., Security Hardening, Test Coverage, DX)
- **Task:** Concrete, actionable item


---

## Sprint 1: Security Hardening & Core Coverage

### Epic: Secrets Management & RBAC

- **[P0][M][Security]** Migrate secrets from `.env` to Vault or secret manager
  - Remove plaintext secrets from repo
  - Update config loading logic to support Vault
- **[P0][M][Backend]** Audit and expand RBAC coverage and negative tests (`app/auth/rbac.py`, `tests/`)
- **[P1][S][Backend]** Harden input validation on all API endpoints (add pydantic validation)
- **[P1][S][Backend]** Audit and scrub logs for sensitive info (loguru config, log statements)


### Epic: Dependency & License Safety

- **[P2][S][Security]** Add trivy, bandit, and safety checks to CI for Python deps (`requirements.txt`)
- **[P2][S][Security]** Review all dependencies for license compliance; add LICENSE file


---

## Sprint 2: Testing, Observability, and Onboarding

### Epic: Test Coverage & CI

- **[P1][M][QA]** Expand unit and integration test coverage (critical flows in `app/`, `tests/`)
- **[P1][S][QA]** Add/expand `pytest --cov` and coverage badge to CI
- **[P1][M][QA]** Add negative/edge case tests for RBAC, input validation, and agent flows


### Epic: Observability & SLOs

- **[P3][M][SRE]** Expand metrics/tracing (Prometheus, OpenTelemetry); document SLOs/SLIs (`observability/`)
- **[P3][S][SRE]** Add alerting rules and dashboards for key metrics


### Epic: Developer Experience

- **[P2][S][DevRel]** Improve README and onboarding docs (quickstart, setup, env)
- **[P2][S][DevRel]** Add setup scripts (`make setup`, devcontainer.json)


---

## Sprint 3: Refactoring & Compliance

### Epic: Maintainability & Refactor

- **[P2][M][Backend]** Refactor large/complex modules for SRP and readability (`app/agents/`, `app/tasks/`)
- **[P2][S][Backend]** Remove dead/unused code (legacy flows, agents)


### Epic: Compliance & Production Hardening

- **[P3][M][Security]** Review and update all compliance docs (SOC2/OWASP mapping)
- **[P3][M][Backend]** Harden Docker/infra for production (docker-compose, resource limits)
- **[P3][S][Backend]** Review and document all APIs (OpenAPI, docstrings)


---

## Sprint 4+: Continuous Improvement
- Ongoing: Monitor dependency risks, update SLOs/SLIs, onboard new contributors, review security posture quarterly.

---

## Task Table (Summary)
| Priority | Task                                | File/Area                        | Effort | Owner    |
|----------|-------------------------------------|----------------------------------|--------|----------|
| P0       | Migrate secrets to Vault            | .env, config, scripts            | M      | Security |
| P0       | Expand RBAC & negative tests        | app/auth/rbac.py, tests/         | M      | Backend  |
| P1       | Input validation everywhere         | app/api/, app/agents/            | S      | Backend  |
| P1       | Audit logs for sensitive info       | app/, loguru config              | S      | Backend  |
| P1       | Expand test coverage & CI           | tests/, app/                     | M      | QA       |
| P2       | Add trivy/bandit/safety checks      | requirements.txt, CI             | S      | Security |
| P2       | Improve onboarding docs/scripts     | README.md, scripts/, devcontainer| S      | DevRel   |
| P2       | Refactor large modules              | app/agents/, app/tasks/          | M      | Backend  |
| P3       | Expand metrics/tracing/SLO docs     | observability/, app/monitoring/  | M      | SRE      |
| P3       | Harden Docker/infra for prod        | docker-compose*, Dockerfile      | M      | Backend  |
| P3       | Review/update compliance docs       | observability/, SECURITY_GAP*    | M      | Security |

---

## Notes
- Each sprint may overlap for urgent P0/P1 items.
- Owners: Security, Backend, QA, SRE, DevRel.
- Review roadmap quarterly or after major releases.
