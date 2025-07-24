# Secret Rotation Guide

This guide explains how to rotate credentials stored in Vault and update services.

## Celery Tasks

The following tasks under `app.tasks.secret_rotation` rotate secrets:

- `rotate_minio_credentials`
- `rotate_minio_root_credentials`
- `rotate_database_password`
- `rotate_jwt_secret`
- `rotate_api_keys`

Execute a task manually using Celery:

```bash
celery -A app.tasks.celery_app call app.tasks.secret_rotation.rotate_minio_credentials
```

These tasks can also be scheduled via Celery beat.

## scripts/rotate_minio_secrets.sh

For a quick rotation of the MinIO access keys run:

```bash
bash scripts/rotate_minio_secrets.sh
```

The script calls `rotate_minio_secrets.py` which updates Vault and prints `export` commands so you can refresh Docker secrets or your `.env` file.

## Updating Other Secrets

Use the same pattern to rotate other credentials. Either invoke the Celery tasks above or create helper scripts that call `VaultClient.rotate_secret()` for the desired keys. After rotation, redeploy any services that rely on those secrets so they pick up the new values.
