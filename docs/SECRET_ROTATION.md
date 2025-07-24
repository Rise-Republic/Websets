# Secret Rotation Guide

This document explains how to rotate credentials used by WebSet Miner.

## Running Celery Tasks

Secret rotation tasks are defined in `app.tasks.secret_rotation` and scheduled by Celery beat. To execute them manually:

```bash
celery -A app.tasks.celery_app call app.tasks.secret_rotation.rotate_minio_credentials
celery -A app.tasks.celery_app call app.tasks.secret_rotation.rotate_minio_root_credentials
```

These tasks update the MinIO keys stored in Vault and can be run on demand.

## Using `rotate_minio_secrets.sh`

The helper script [`scripts/rotate_minio_secrets.sh`](../scripts/rotate_minio_secrets.sh) rotates the local MinIO credentials via Vault and exports them to the shell:

```bash
bash scripts/rotate_minio_secrets.sh
```

Run this after setting `VAULT_ADDR` and `VAULT_TOKEN`. The script calls `rotate_minio_secrets.py` which writes the new values back to Vault and prints `export` commands so you can update your environment or Docker secrets.

## Updating Other Secrets

Use the `VaultClient` helper to rotate additional values as needed:

```bash
python - <<'PY'
from app.secrets.vault import VaultClient
client = VaultClient()
client.rotate_secret("secret/websets", "SOME_OTHER_SECRET", length=32)
PY
```

Replace `SOME_OTHER_SECRET` with the key to rotate. Update any running containers or secrets managers with the new values.
