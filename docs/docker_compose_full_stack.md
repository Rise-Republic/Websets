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

This creates a `certs/` directory containing `ca.crt` plus client and server
certificates for each service (`app`, `minio`, `vault`, `redis`, `qdrant`, and
`weaviate`). These files are mounted into the containers by
`docker-compose.yml`.

## Start the Stack

With the certificates in place, start all services:

```bash
make dev
```
This wrapper command generates certificates if needed, builds the containers,
applies migrations and seeds an initial user before running
`docker compose up -d` under the hood. Set the `SEED_USER_EMAIL` and
`SEED_USER_PASSWORD` environment variables to define the credentials used for
this user.

The compose file launches the API, Celery workers, Redis, PostgreSQL, MinIO (with TLS), Prometheus, Grafana, and optional vector stores. The API will be available at `http://localhost:8000` and MinIO at `https://localhost:9000`.

Use `docker compose logs -f` to watch startup logs. Once all services are healthy you can submit a job via the CLI:

```bash
python scripts/run_job.py "AI startups in Europe hiring ML engineers"
```

For advanced TLS or production cert rotation see [PRODUCTION_DEPLOYMENT.md](../PRODUCTION_DEPLOYMENT.md) and [app/storage/README_minio_tls.md](../app/storage/README_minio_tls.md).
