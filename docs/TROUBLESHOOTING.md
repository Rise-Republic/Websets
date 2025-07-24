# Troubleshooting

This guide lists common issues and recovery steps.

## Vault Misconfiguration

- **Symptom:** Application exits with `Failed to read secrets from Vault`.
- **Fix:** Verify `VAULT_ADDR` and `VAULT_TOKEN`. If developing locally, set `DISABLE_VAULT_FOR_LOCAL_DEV=true` and ensure `.env` contains the required secrets.

## Certificate Errors

- **Symptom:** `SSL: CERTIFICATE_VERIFY_FAILED` when accessing MinIO or other services.
- **Fix:** Check that `MINIO_CA_CERT`, `MINIO_CLIENT_CERT`, and `MINIO_CLIENT_KEY` point to valid files. Regenerate certs using `scripts/generate_mtls_certs.sh` if needed.

## Database Migrations

- **Symptom:** Application fails to start with `relation "jobs" does not exist`.
- **Fix:** Run `alembic upgrade head` to apply pending migrations. See [MIGRATIONS.md](MIGRATIONS.md) for details.

## Celery Hangups

- **Symptom:** Jobs remain in `PENDING` state.
- **Fix:** Ensure Redis is reachable (`redis-cli ping`) and that workers are running (`docker-compose ps worker`). Restart workers if necessary.

## Interpreting Logs and Metrics

- Use `docker-compose logs <service>` to view service output.
- Prometheus metrics at `/health/metrics` include job counters and latencies.
- Look for spikes in `job_failures_total` or high `queue_latency_seconds` to identify bottlenecks.

