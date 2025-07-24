# Operational Runbook

This runbook covers day‑to‑day operations, health checks and scaling procedures for WebSet Miner.

## Health Checks

The API exposes health endpoints which are used for self‑healing container restarts:

- `GET /health/` – basic check
- `GET /health/detailed` – component status (database, Redis, vector store)
- `GET /health/readiness` – used by Kubernetes readiness probe
- `GET /health/liveness` – used by Kubernetes liveness probe

Containers are configured with `restart: unless-stopped` in `docker-compose.yml` so failed services automatically restart.

## Scaling Workers

Celery workers handle background jobs. Scale them by increasing the `--concurrency` flag or launching additional containers:

```bash
docker-compose up -d --scale worker=4
```

Monitor queue lengths with `flower` or Prometheus metrics exposed at `/health/metrics`.

## Monitoring Metrics

Key metrics include:

- Job start/completion/failure counters
- Crawl throughput and average latency
- Celery queue length and worker uptime
- API request durations

Metrics are scraped by Prometheus. Import `monitoring/grafana/dashboards/websets_overview.json` into Grafana to visualize them.

## Observability Smoke Tests

Run a quick check that metrics and tracing infrastructure are reachable:

```bash
pytest -m smoke
```

This executes `tests/smoke/test_observability.py` which verifies the `/health/metrics` endpoint and the OTLP collector health endpoint.

## Backup and Restore

PostgreSQL data is backed up with `scripts/backup_db.sh`. Example:

```bash
./scripts/backup_db.sh backups/websets-$(date +%F).sql
```

Restore using:

```bash
docker exec -i websets-db-1 psql -U postgres -d websets < backup.sql
```

Redis is mostly ephemeral but can be saved using `redis-cli BGSAVE`. For vector data (Qdrant/Weaviate) back up the `data/` volume or use the database's snapshot feature.

## Secret Rotation

Credentials in Vault should be rotated regularly. Celery beat runs tasks in
`app.tasks.secret_rotation` to update MinIO credentials, the database password,
JWT secrets and API keys. See [Secret Rotation Guide](SECRET_ROTATION.md) for
manual rotation steps and helper scripts.

## Smoke Tests

Run the smoke test suite after deploying new versions or performing maintenance to ensure that the API and UI still work end‑to‑end.

```bash
pytest -m smoke            # backend checks
npm run system -- --grep \@smoke  # frontend checks
```

Successful runs end with `N passed` and exit code `0`. Any failure should be investigated immediately.

Troubleshooting steps:

1. View the [Websets Overview](http://grafana.example.com/d/websets-overview) dashboard for error spikes or failed health checks.
2. Open Grafana's **Explore** tab and search Tempo/Jaeger traces using the IDs printed in the test output.

Rerun the tests once issues are resolved to confirm recovery.
