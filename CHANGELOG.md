# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Breaking changes must be called out under a `Removed` or `Changed` section with clear upgrade instructions.

## [Unreleased]
- Work in progress.

### Added
- Python-based `generate_mtls_certs.py` with shell wrapper.
- `VaultClient.fetch_all` helper and accompanying tests.
- Unit tests for certificate generation script.

### Changed
- `dev_stack.sh` now calls the Python certificate generator.
- Documentation updated to reference the new script.

### Template
Use the sections below when preparing a release.

```
## [X.Y.Z] - YYYY-MM-DD
### Added
-
### Changed
-
### Fixed
-
### Removed
-
```

## [0.2.0] - 2025-07-24
### Added
- Encryption at rest for PostgreSQL and MinIO
- Blue/green deployment script and rollback guidance
- Vault service integration with mTLS across services
- Production deployment and container hardening docs
- Authentication endpoints documentation
- Backup script and disaster recovery runbook
- CI pipelines for tests, security scans and coverage
- Unit tests for EmbeddingGenerator and MetricsCollector
- JSON structured logging support
- Terraform modules for infrastructure

### Changed
- Docker Compose updated to version 3.9 with health checks
- Secrets moved out of configs and validated via Vault

## [0.1.0] - 2025-07-23
### Added
- Initial release of WebSet Miner with core agents, API endpoints and Docker deployment.
- Continuous integration for tests, security scans and Docker build.

