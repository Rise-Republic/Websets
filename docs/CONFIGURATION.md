# Configuration

This document lists important environment variables and configuration files. All secrets are managed through Vault and loaded at runtime unless `DISABLE_VAULT_FOR_LOCAL_DEV=true` is set.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
|`VAULT_ADDR`|Vault server URL|`http://localhost:8200`|
|`VAULT_SECRET_PATH`|Path within Vault for secrets|`secret/data/websets`|
|`DATABASE_URL`|PostgreSQL connection string|–|
|`REDIS_URL`|Redis connection|`redis://redis:6379/0`|
|`CELERY_BROKER_URL`|Celery broker|`redis://redis:6379/1`|
|`CELERY_RESULT_BACKEND`|Celery result backend|`redis://redis:6379/2`|
|`JWT_SECRET_KEY`|JWT signing secret|–|
|`OPENAI_API_KEY`|OpenAI API key|–|
|`ANTHROPIC_API_KEY`|Anthropic API key|–|
|`MINIO_ENDPOINT`|MinIO URL|`https://minio:9000`|
|`MINIO_BUCKET`|Bucket name|`websets-data`|
|`MINIO_CLIENT_CERT`|Client certificate when using mTLS|–|
|`MINIO_CLIENT_KEY`|Client key when using mTLS|–|
|`MINIO_CA_CERT`|CA certificate when using mTLS|–|
|`MAX_CONCURRENT_CRAWLS`|Number of parallel crawlers|`5`|
|`REQUEST_DELAY_MS`|Delay between requests|`1000`|
|`USER_AGENT`|Crawler user agent string|`WebSetMiner/1.0`|
|`LOG_LEVEL`|Logging level|`INFO`|

Example `.env` entries:

```env
VAULT_ADDR=http://localhost:8200
VAULT_SECRET_PATH=secret/data/websets
DISABLE_VAULT_FOR_LOCAL_DEV=true
DATA_DIR=./data
MAX_CONCURRENT_CRAWLS=5
LOG_LEVEL=DEBUG
```

Use `python fetch_vault_env.py > .env` to write secrets from Vault into the `.env` file for local usage.

## mTLS Setup

Generate a certificate authority and client certificates with:

```bash
scripts/generate_mtls_certs.sh mydomain.local
```

Mount the resulting `certs/` directory into each container and set:

```env
MINIO_CA_CERT=/certs/ca.crt
MINIO_CLIENT_CERT=/certs/app.crt
MINIO_CLIENT_KEY=/certs/app.key
```

Unset these variables to disable mTLS.

## Docker Compose Overrides

- `docker-compose.yml` – default development stack.
- `docker-compose.monitoring.yml` – adds Prometheus and Grafana.
- `docker-compose.prod.yml` *(not committed)* – example production overrides. Use environment variables for database credentials and enable mTLS.

Override the compose file when starting services:

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Object Storage Path Layout

Uploaded artifacts are stored in MinIO using a tenant-aware prefix. The full key
is generated as:

```text
<tenant_id>/<object_name>
```

Use the `tenant_object_name` helper from `app.storage.minio_client` to build
these names when calling `upload_file_encrypted` or `download_file`.

