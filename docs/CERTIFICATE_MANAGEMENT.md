# Certificate Management

This project uses mutual TLS between internal services. All certificates are stored in the `certs/` directory by default. The location can be overridden with the `CERT_DIR` environment variable.

## Checking Expiration

Run `scripts/check_cert_expiration.py` to list certificates that will expire soon. The script reads `CERT_DIR` and warns when a certificate expires within `CERT_EXPIRY_WARN_DAYS` (default 30) days.

```bash
python scripts/check_cert_expiration.py
```

## Rotation

Self-signed certificates can be regenerated with `scripts/generate_mtls_certs.py`. Set `CERT_DIR` to control the output path.

```bash
CERT_DIR=/etc/websets/certs scripts/generate_mtls_certs.py
```

The Celery beat task `check_certificate_expiration` logs warnings daily so operators know when to rotate certificates.
