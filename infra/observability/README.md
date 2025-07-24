# Observability Infrastructure

This directory contains Terraform modules and Helm configuration for deploying the observability stack described in [observability/infra_setup.md](../../observability/infra_setup.md).

Components deployed:

- **OpenTelemetry Collector**
- **Prometheus** with custom recording and alerting rules
- **Grafana** with preloaded dashboards
- **Alertmanager**

RBAC manifests for each component live in `rbac/`.
