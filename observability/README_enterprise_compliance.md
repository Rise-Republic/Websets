# Enterprise Compliance for Observability

This document outlines how the observability stack meets SOC 2, HIPAA, and ISO 27001 requirements.

## SOC 2
The observability stack covers the Trust Services Criteria:
- **Security** – Audit logging with tamper-proof, signed logs
- **Availability** – SLO/SLI tracking and alerting
- **Confidentiality** – RBAC for log and trace access
- Incident response runbooks for operational continuity

## HIPAA

- Encrypted log storage and transmission
- Data retention and legal hold policies
- Role-based access for PHI queries

## ISO 27001

- Config-as-Code for all observability components
- Peer review and change management workflows
- Automated compliance checks in CI/CD

## OWASP Top 10 Mapping

- **A01 – Broken Access Control**: RBAC enforced across dashboards and alerting
- **A02 – Cryptographic Failures**: Logs transmitted and stored with TLS and encryption at rest
- **A03 – Injection**: Input validation logged and traced for visibility
- **A05 – Security Misconfiguration**: Configuration drift detected via CI/CD checks
