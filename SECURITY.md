# Security Policy

If you believe you have found a vulnerability, report it through GitHub Issues using the security template or email security@websets.example.com.

## Supported Versions

Only the latest minor release receives security patches.

## Reporting a Vulnerability

1. Create an issue using the **Security report** template.
2. Provide steps to reproduce and any relevant logs.
3. Allow 90 days for investigation and remediation before public disclosure.

## Threat Model

- **External attackers** targeting API endpoints, authentication, or data stores.
- **Multi-tenant data leakage** via mis-scoped queries or missing RLS.
- **Supply-chain risks** through third-party dependencies and container images.
- **Insider threats** abusing elevated privileges.

## Mitigations

- Enforced tenant scoping and PostgreSQL Row Level Security.
- Rate limiting, CSRF protection, and strict CORS.
- Docker images run as non-root and undergo vulnerability scanning.
- NetworkPolicies restrict pod communication.

## Responsible Disclosure

Please include proof-of-concept steps and affected components. We will confirm receipt within 72 hours and provide status updates at 30 and 60 days.
