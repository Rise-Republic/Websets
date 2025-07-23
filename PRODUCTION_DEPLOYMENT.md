# Production Deployment Guide

This guide covers best practices for deploying WebSet Miner securely in a production environment.

## HTTPS Configuration

- **Terminate TLS at a reverse proxy.** Use a load balancer such as Nginx or Traefik in front of the FastAPI server.
- **Automate certificate management.** Obtain certificates from Let's Encrypt with certbot or your cloud provider and renew them automatically.
- **Enforce HTTPS.** Redirect all HTTP traffic to HTTPS and use HSTS headers to prevent downgrade attacks.
- **Expose the FastAPI app on an internal network only.** The container should listen on a private interface while the proxy handles public TLS.

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
- **Drop unnecessary Linux capabilities** and set the filesystem to read-only where possible.
- **Keep dependencies up to date** and scan images with tools like `trivy` during CI/CD.
- **Store secrets outside the image.** Inject them at runtime using Docker secrets or Vault.

Example Docker run command with tightened security:
```bash
docker run -d \
  --read-only \
  --cap-drop=ALL \
  --user appuser \
  --env-file .env \
  webset-miner:latest
```

Following these practices helps ensure the application is delivered over HTTPS and that containers are resilient against common attacks.
