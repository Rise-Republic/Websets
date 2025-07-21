# Structured Audit Logging Setup

## Overview
This guide covers JSON log standardization, cryptographic signing, centralization in ELK/OpenSearch, RBAC, and retention policies.

## Steps
1. Standardize JSON log format across all services.
2. Implement cryptographic signing/digesting of logs (hash+HMAC).
3. Ship logs to ELK/OpenSearch using Filebeat/Fluentd sidecars.
4. Tag logs with tenant, service, and trace IDs.
5. Integrate MinIO, CI/CD, and API gateway logs into the pipeline.
6. Enforce role-based access in OpenSearch.
7. Set up GDPR/HIPAA-compliant retention and legal hold policies.

## Automation
- Config-as-Code for log pipeline (Helm, Terraform).
- CI/CD validation for log format and signing.
- Peer review for log schema changes.
