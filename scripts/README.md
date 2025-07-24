# Helper Scripts

This directory contains various utility scripts used during development and deployment of WebSet Miner.

## Shell scripts

- `setup.sh` - bootstrap the local development environment.
- `test.sh` - run backend and frontend test suites.
- `blue_green_deploy.sh` - perform a basic blue/green Kubernetes deployment.
- `kubectl rollout undo deployment/webset-miner` - quick rollback without blue/green.
- `apply_minio_policy.sh` - apply the MinIO bucket policy from `app/storage/minio_policy.json`.
- `audit_minio_policy.sh` - print and log current MinIO bucket policies.
- `rotate_minio_secrets.sh` - rotate local MinIO credentials.
- `generate_mtls_certs.sh` - generate a shared CA and per-service certificates
  (`app`, `minio`, `vault`, `redis`, `qdrant`, `weaviate`).

## Python scripts

- `run_job.py` - CLI helper to create and optionally execute a mining job.
- `test_vault.py` - simple connectivity check for Vault secrets.
- `generate_openapi_spec.py` - export the FastAPI OpenAPI spec to `openapi.json`.

See `README_minio_security.md` for additional security related notes around the MinIO scripts.
