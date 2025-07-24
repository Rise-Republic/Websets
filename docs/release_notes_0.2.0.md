# WebSet Miner 0.2.0 Release Notes

This release focuses on hardening the platform for production use and expanding test coverage.

## Highlights
- **Encryption at Rest** for PostgreSQL and MinIO using customer managed keys.
- **Vault Integration** with mTLS between all internal services.
- **Blue/Green Deployments** via `scripts/blue_green_deploy.sh` with rollback instructions.
- **Production Deployment Guide** detailing container hardening best practices.
- **CI Pipelines** running tests, coverage checks and CodeQL security scans.
- **Additional Unit Tests** for key modules and improved login flows.
- **Terraform Modules** added for baseline infrastructure.
- **Structured JSON Logging** to aid log aggregation and monitoring.

Refer to `CHANGELOG.md` for the complete list of changes.
