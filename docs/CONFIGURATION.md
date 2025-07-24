# Configuration

This document lists environment variables and configuration files used by the project.  Configuration values are read in the following order so that later sources override earlier ones:

1. Values defined in a local `.env` file.
2. Environment variables set in any `docker-compose*.yml` file.
3. Secrets loaded from Vault.

All secrets are managed through Vault and loaded at runtime unless `DISABLE_VAULT_FOR_LOCAL_DEV=true` is set.
When running in Docker, secret files mounted under `/run/secrets/<NAME>` are
also read automatically before falling back to environment variables. This
allows sensitive values to be injected via Docker secrets without appearing in
the compose file.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
|`VAULT_ADDR`|Vault server URL|`http://localhost:8200`|
|`VAULT_TOKEN`|Vault token|–|
|`VAULT_SECRET_PATH`|Path within Vault for secrets|`secret/data/websets`|
|`DISABLE_VAULT_FOR_LOCAL_DEV`|Bypass Vault when true|`false`|
|`DATA_DIR`|Local data directory|`./data`|
|`VECTOR_STORE_PATH`|Vector store location|`./data/vector_store`|
|`VECTOR_STORE_PROVIDER`|Vector store backend|`chromadb`|
|`DATABASE_URL`|PostgreSQL connection string|–|
|`REDIS_URL`|Redis connection|`redis://redis:6379/0`|
|`CELERY_BROKER_URL`|Celery broker|`redis://redis:6379/1`|
|`CELERY_RESULT_BACKEND`|Celery result backend|`redis://redis:6379/2`|
|`OPENAI_API_KEY`|OpenAI API key|–|
|`ANTHROPIC_API_KEY`|Anthropic API key|–|
|`JWT_SECRET_KEY`|JWT signing secret|–|
|`JWT_ALGORITHM`|JWT algorithm|`HS256`|
|`ACCESS_TOKEN_EXPIRE_MINUTES`|Access token lifetime|`30`|
|`AUTH0_DOMAIN`|Auth0 domain|–|
|`AUTH0_CLIENT_ID`|Auth0 client ID|–|
|`AUTH0_CLIENT_SECRET`|Auth0 client secret|–|
|`AUTH0_AUDIENCE`|Auth0 audience|–|
|`AUTH0_ISSUER`|Auth0 issuer URL|–|
|`SMTP_HOST`|SMTP server host|`localhost`|
|`SMTP_PORT`|SMTP server port|`25`|
|`SMTP_USERNAME`|SMTP username|–|
|`SMTP_PASSWORD`|SMTP password|–|
|`EMAIL_FROM`|Default sender email|`no-reply@example.com`|
|`PASSWORD_RESET_URL`|Base URL for password reset links|`http://localhost`|
|`MAX_CONCURRENT_CRAWLS`|Number of parallel crawlers|`5`|
|`REQUEST_DELAY_MS`|Delay between requests|`1000`|
|`USER_AGENT`|Crawler user agent string|`WebSetMiner/1.0`|
|`ENVIRONMENT`|Runtime environment|`development`|
|`LOG_LEVEL`|Logging level|`INFO`|
|`ENABLE_TRACING`|Enable OpenTelemetry|`false`|
|`OTLP_ENDPOINT`|OTLP collector endpoint|`http://localhost:4318`|
|`ALLOWED_ORIGINS`|Comma separated CORS origins|`http://localhost:3000,...`|
|`MINIO_ENDPOINT`|MinIO URL|`http://localhost:9000`|
|`MINIO_BUCKET`|Bucket name|`websets-data`|
|`MINIO_ACCESS_KEY`|MinIO access key|`minioadmin`|
|`MINIO_SECRET_KEY`|MinIO secret key|`minioadmin`|
|`MINIO_CLIENT_CERT`|Client certificate when using mTLS|–|
|`MINIO_CLIENT_KEY`|Client key when using mTLS|–|
|`MINIO_CA_CERT`|CA certificate when using mTLS|–|
|`MINIO_VAULT_PATH`|Vault path for rotating MinIO creds|`secret/websets`|
|`OBJECT_STORAGE_PROVIDER`|Object store provider|`local`|
|`AWS_ACCESS_KEY_ID`|AWS access key|–|
|`AWS_SECRET_ACCESS_KEY`|AWS secret key|–|
|`AWS_REGION`|AWS region|`us-east-1`|
|`S3_BUCKET_NAME`|S3 bucket|–|
|`GCS_BUCKET_NAME`|Google Cloud bucket|–|
|`GCS_CREDENTIALS_PATH`|Path to GCS creds JSON|–|
|`PINECONE_API_KEY`|Pinecone API key|–|
|`PINECONE_ENVIRONMENT`|Pinecone environment|`us-east1-gcp`|
|`WEAVIATE_URL`|Weaviate URL|`http://localhost:8080`|
|`WEAVIATE_API_KEY`|Weaviate API key|–|
|`QDRANT_URL`|Qdrant URL|–|
|`QDRANT_API_KEY`|Qdrant API key|–|

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

Example override for local development (`docker-compose.override.yml`):

```yaml
services:
  app:
    environment:
      MINIO_ENDPOINT: https://minio:9000
      MINIO_CA_CERT: /certs/ca.crt
      MINIO_CLIENT_CERT: /certs/app.crt
      MINIO_CLIENT_KEY: /certs/app.key
    volumes:
      - ./certs:/certs:ro
```

For production you might mount certificates from a secure location and point to the public MinIO endpoint:

```yaml
# docker-compose.prod.yml
services:
  app:
    environment:
      MINIO_ENDPOINT: https://minio.example.com:9000
      MINIO_CA_CERT: /etc/ssl/prod/ca.crt
      MINIO_CLIENT_CERT: /etc/ssl/prod/app.crt
      MINIO_CLIENT_KEY: /etc/ssl/prod/app.key
    volumes:
      - /etc/ssl/prod:/etc/ssl/prod:ro
```

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

