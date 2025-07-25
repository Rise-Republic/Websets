# DDoS Mitigation Guide

This document outlines how Websets mitigates denial-of-service attacks.

## Application Layer Protections

- **Rate limiting middleware** in `app/middleware/rate_limiting.py` uses Redis to throttle requests per IP, user, and tenant.
- Clients exceeding the limits receive a `429` response with a `Retry-After` header.

## Network and Edge Defenses

- Deploy a reverse proxy such as **Nginx** or **Traefik** with request and connection limiting enabled. Example Nginx snippet:

```nginx
limit_req_zone $binary_remote_addr zone=mapi:10m rate=10r/s;
server {
    location / {
        limit_req zone=mapi burst=20 nodelay;
        proxy_pass http://webset-miner:8000;
    }
}
```

- Use a web application firewall or CDN (e.g. Cloudflare, AWS Shield, Cloud Armor) to absorb volumetric attacks.
- Configure provider-level DDoS protections and IP reputation filtering.

## Monitoring

- Track HTTP 429 responses and request volumes in Prometheus to detect spikes.
- Alert on sustained high request rates or when edge rules are triggered.

Combined with incident response procedures, these controls help maintain availability during malicious traffic surges.
