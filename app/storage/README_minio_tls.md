# MinIO TLS & Access Logging Setup

## TLS Configuration
- Generate TLS certificates (use Let’s Encrypt, cert-manager, or your CA).
- Mount certs in MinIO container:
  - `/certs/private.key`
  - `/certs/public.crt`
- Update `docker-compose.yml`:
  ```yaml
  minio:
    ...
    volumes:
      - ./certs:/certs
    environment:
      MINIO_SERVER_URL: https://minio:9000
  ```
- Restart MinIO. Verify HTTPS at `https://localhost:9000`.

## Cert Rotation
- Automate renewal with cron or cert-manager.
- Restart MinIO after cert update.

## Access Logging
- Enable server access logs in MinIO config.
- Archive logs to a secure bucket or external SIEM.

## Firewall/IP Allowlist
- Restrict MinIO access to trusted IPs/networks via firewall/security group.

## Compliance Checklist
- TLS enabled and auto-rotated
- Access logs archived and reviewed
- IP allowlist/firewall enforced
