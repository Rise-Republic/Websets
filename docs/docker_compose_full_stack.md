# Running the Full Stack with Docker Compose

This guide explains how to bring up all services locally using Docker Compose and configure TLS certificates for internal communication.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- No additional setup is required; `make dev` seeds Vault automatically.


## Start the Stack

Start all services with a single command:

```bash
make dev
```
This wrapper command generates certificates if needed, builds the containers,
applies migrations and seeds an initial user before running
`docker compose up -d` under the hood. Set the `SEED_USER_EMAIL` and
`SEED_USER_PASSWORD` environment variables to define the credentials used for
this user.

The compose file launches the API, Celery workers, Redis, PostgreSQL, MinIO (with TLS), and optional vector stores. Start the monitoring services with:

```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up
```

The API will be available at `http://localhost:8000` and MinIO at `https://localhost:9000`.

Use `docker compose logs -f` to watch startup logs. Once all services are healthy you can submit a job via the CLI:

```bash
python scripts/run_job.py "AI startups in Europe hiring ML engineers"
```

For advanced TLS or production cert rotation see [PRODUCTION_DEPLOYMENT.md](../PRODUCTION_DEPLOYMENT.md) and [app/storage/README_minio_tls.md](../app/storage/README_minio_tls.md).
