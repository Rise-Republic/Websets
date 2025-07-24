# Docker Secrets

Store sensitive values like database and MinIO credentials as Docker secrets.
Secrets are typically pulled from Vault and loaded using `docker secret create`.
The individual secret files shown here are ignored and should not be committed.
For example:

```bash
vault kv get -field=MINIO_ROOT_USER secret/websets | \
  docker secret create minio_root_user -
vault kv get -field=MINIO_ROOT_PASSWORD secret/websets | \
  docker secret create minio_root_password -
```
