# Threat Model

This document summarizes the key security risks for Websets and the mitigations currently in place.

## Risks

- **Credential exposure** – API keys or database passwords may leak from configuration or logs.
- **Unauthorized data access** – improper access controls could allow reading or modifying datasets.
- **Supply chain attacks** – third‑party dependencies could introduce malicious code.
- **Denial of service** – abuse of the mining API could exhaust resources.
- **Data tampering** – attackers might attempt to alter stored results or logs.

## Mitigations

- Secrets are pulled from Vault and never committed to the repository.
- JWT authentication and role based access control guard all API endpoints.
- Dependencies are scanned in CI with Safety and Dependabot keeps versions patched.
- Rate limiting middleware caps the number of requests per user.
- Audit logs are stored immutably and signed to detect tampering.
