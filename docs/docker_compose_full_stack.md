# Running the Full Stack with Docker Compose

This guide explains how to bring up all services locally using Docker Compose and configure TLS certificates for internal communication.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Vault with the secrets from `vault_secrets_template.json` loaded (see [README](../README.md) for details)

## Generate Certificates

For local development you can use self‑signed certificates for mutual TLS between the application and MinIO. Run the helper script from the project root:

```bash
scripts/generate_mtls_certs.sh
```

This creates a `certs/` directory containing `ca.crt`, `app.crt`, `app.key`, `minio.crt`, and `minio.key`. These files are mounted into the containers by `docker-compose.yml`.

## Start the Stack

With the certificates in place, start all services:

```bash
docker compose up -d
```

The compose file launches the API, Celery workers, Redis, PostgreSQL, MinIO (with TLS), Prometheus, Grafana, and optional vector stores. The API will be available at `http://localhost:8000` and MinIO at `https://localhost:9000`.

Use `docker compose logs -f` to watch startup logs. Once all services are healthy you can submit a job via the CLI:

```bash
python scripts/run_job.py "AI startups in Europe hiring ML engineers"
```

For advanced TLS or production cert rotation see [PRODUCTION_DEPLOYMENT.md](../PRODUCTION_DEPLOYMENT.md) and [app/storage/README_minio_tls.md](../app/storage/README_minio_tls.md).
