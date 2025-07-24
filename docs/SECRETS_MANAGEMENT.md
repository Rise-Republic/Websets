# Secrets Management and Rotation

This project uses **HashiCorp Vault** to securely store and rotate all sensitive values such as API keys, database passwords and JWT signing keys. The following practices keep secrets safe across all environments:

## Centralized Secrets Storage
- Vault is the single source of truth for credentials.
- Access to secrets is restricted by policy and tokens are scoped to the minimal permissions required.
- `app/secrets/vault.py` provides a simple client for fetching secrets at runtime.

## Automated Rotation
- Celery beat schedules tasks in `app.tasks.secret_rotation` to rotate MinIO credentials, the database password, JWT secrets and API keys.
- A GitHub Actions workflow (`.github/workflows/vault-rotate.yml`) performs an additional weekly rotation.
- After each rotation, dependent services load the new values from Vault automatically.

## Minimal Secrets Exposure
- Secrets are injected via environment variables or Docker secrets at runtime and never committed to the repository.
- Local development can generate a `.env` file using `fetch_vault_env.py`.
- Services read secrets from `/run/secrets/<NAME>` when running in Docker.

## Audit & Access Control
- Vault access is logged and can be audited to track which service retrieved or updated a secret.
- Only designated CI jobs and service accounts may modify credentials.

## Testing
- Unit tests cover the Vault client and secret rotation tasks (`tests/unit/test_vault_rotation.py` and `tests/unit/test_secret_rotation_tasks.py`).
- CI executes these tests to ensure secrets are loaded and rotated correctly.
