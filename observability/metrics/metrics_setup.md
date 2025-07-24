# Metrics & Dashboarding Setup

## Overview
This guide describes exposing Prometheus metrics, provisioning Grafana dashboards, and enabling multi-tenancy and drill-down.

## Steps
1. Expose Prometheus metrics in all services (latency, error rate, volume, custom metrics).
2. Instrument Python/Node services with OpenTelemetry and export metrics via the Prometheus exporter.
3. Annotate the Kubernetes Service with Prometheus scrape settings:
   ```yaml
   metadata:
     annotations:
       prometheus.io/scrape: "true"
       prometheus.io/path: "/health/metrics"
       prometheus.io/port: "8000"
   ```
4. Deploy Prometheus and Grafana via Helm. Mount `monitoring/prometheus/rules/key_metrics.yml` for alerting rules.
5. Create version-controlled Grafana dashboards (JSON/Terraform/Jsonnet). Example dashboard JSON lives in `monitoring/grafana/dashboards/websets_overview.json`.
6. Auto-provision dashboards per environment.
7. Enable multi-tenancy, time comparison, and drill-down.
8. Integrate trace IDs and SLO metrics into dashboards.
9. Import `monitoring/grafana/dashboards/websets_overview.json` into Grafana to see Websets metrics.
10. Configure RBAC via `monitoring/grafana/provisioning/access-control` so only authorized teams can modify dashboards.

## Automation
- Terraform/Jsonnet for dashboard provisioning.
- CI/CD pipeline for metrics endpoint checks.
- Self-service dashboard templates.
