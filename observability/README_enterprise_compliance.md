# Enterprise Compliance for Observability

This document outlines how the observability stack meets SOC 2, HIPAA, and ISO 27001 requirements.

## SOC 2

- Audit logging with tamper-proof, signed logs
- RBAC for log/query access
- Alerting and incident response runbooks
- SLO/SLI governance and error budget tracking

## HIPAA

- Encrypted log storage and transmission
- Data retention and legal hold policies
- Role-based access for PHI queries

## ISO 27001

- Config-as-Code for all observability components
- Peer review and change management workflows
- Automated compliance checks in CI/CD
