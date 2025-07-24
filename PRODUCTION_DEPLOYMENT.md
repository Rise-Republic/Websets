# Production Deployment Guide

This guide covers best practices for deploying WebSet Miner securely in a production environment.

## HTTPS Configuration

- **Terminate TLS at a reverse proxy.** Use a load balancer such as Nginx or Traefik in front of the FastAPI server.
- **Automate certificate management.** Obtain certificates from Let's Encrypt with certbot or your cloud provider and renew them automatically.
- **Enforce HTTPS.** Redirect all HTTP traffic to HTTPS and use HSTS headers to prevent downgrade attacks.
- **Expose the FastAPI app on an internal network only.** The container should listen on a private interface while the proxy handles public TLS.
- **Enable application enforcement.** `HTTPSRedirectMiddleware` and `SecurityMiddleware` are included in `app/main.py` to force HTTPS and add HSTS/X-Frame-Options headers.

## mTLS Between Services

 - Generate a shared certificate authority and client certificates using `scripts/generate_mtls_certs.py`.
- Mount the certificates into each service container (`vault`, `redis`, `qdrant`, `weaviate`, `minio`, and the app) and configure `MINIO_CA_CERT`, `MINIO_CLIENT_CERT`, and `MINIO_CLIENT_KEY` for the app. Set `MINIO_ENDPOINT=https://minio:9000` so the Python client uses TLS.
If services run on separate nodes, copy the generated certs to each host and mount them so internal traffic is mutually authenticated.
- The provided Celery task `rotate_minio_credentials` keeps object storage credentials fresh in Vault.

Example Nginx snippet:
```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://webset-miner:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Container Hardening

- **Use multi-stage builds** to produce a slim runtime image and reduce attack surface.
- **Run as a non-root user** (already configured in the provided Dockerfile).
- **Drop unnecessary Linux capabilities**, apply a hardened seccomp profile, and mount the filesystem read-only (use `--tmpfs /tmp` when writable scratch space is required).
- **Enable the `no-new-privileges` option** so processes cannot gain additional rights even if a binary has the setuid bit.
- **Keep dependencies up to date** and scan images with tools like `trivy` or `dockle` during CI/CD.
- **Sign images with `cosign`** and verify signatures before deploying.
- **Store secrets outside the image.** Inject them at runtime using Docker secrets or Vault.

Example Docker run command with tightened security:
```bash
docker run -d \
  --read-only \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  --security-opt seccomp=seccomp_profile.json \
  --user appuser \
  --tmpfs /tmp \
  --env-file .env \
  webset-miner:latest
```

The `.env` file should contain only non-secret settings. Vault or Docker secrets supply the sensitive credentials.

Following these practices helps ensure the application is delivered over HTTPS and that containers are resilient against common attacks.

## Database Security

- Mount the PostgreSQL data directory on an encrypted volume or use your cloud provider's disk encryption features.
- Use TLS for all database connections by adding `?sslmode=require` to `DATABASE_URL`.
- The compose file sets `POSTGRES_ENCRYPTION_KEY_FILE` so the server uses encrypted storage.

## Object Storage Encryption

- MinIO can automatically encrypt objects at rest.
- Provide a KMS secret via `MINIO_KMS_SECRET_KEY` and a bucket key with `MINIO_SSE_MASTER_KEY`.
- Store these values as Docker secrets referenced by `docker-compose.yml`.
- Ensure `MINIO_KMS_AUTO_ENCRYPTION=on` is enabled so uploads are encrypted by default.

## Backups and Recovery

Regularly dump the PostgreSQL database and keep the files in secure storage. See
[Backups & Disaster Recovery](docs/runbooks/backups.md) for the backup script
and restoration steps.

## Infrastructure Automation

Provision and update infrastructure via Terraform:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

If an apply misbehaves, re-apply the previous commit's configuration or use
`kubectl rollout undo deployment/webset-miner` to roll back the running
application without the blue/green procedure.

### Blue/Green Deployment Script

Use `scripts/blue_green_deploy.sh` to shift traffic between the `webset-miner-blue`
and `webset-miner-green` deployments. The script waits for the new replica set to
finish rolling out and polls Prometheus for a low HTTP error rate before keeping
traffic on the new version. If metrics remain unhealthy within the timeout,
traffic automatically reverts to the previously selected deployment.

```bash
# Deploy the green version and monitor metrics
scripts/blue_green_deploy.sh green
```

Override `PROMETHEUS_URL`, `DEPLOY_TIMEOUT`, or `HEALTH_TIMEOUT` as needed when
invoking the script.
