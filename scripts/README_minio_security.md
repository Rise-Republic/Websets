# MinIO Security Automation Scripts

## Scripts

- `apply_minio_policy.sh`: Applies the bucket policy from JSON to enforce encryption at rest. Run after bucket creation or policy changes.
- `rotate_minio_secrets.sh`: Rotates MinIO credentials and exports them to the environment. Integrate with Vault for production.
- `audit_minio_policy.sh`: Audits current bucket policies and logs them for compliance traceability.

## Usage

```sh
bash scripts/apply_minio_policy.sh
bash scripts/rotate_minio_secrets.sh
bash scripts/audit_minio_policy.sh
```

## Best Practices
- Version all policy JSON files in git.
- Run audit script after every policy change and before compliance reviews.
- Rotate credentials regularly and store them in Vault or a secrets manager.
- Celery tasks rotate MinIO credentials automatically.
- Never hardcode credentials in code or config files.
- Use the Python MinIO client with encryption headers for all uploads.
