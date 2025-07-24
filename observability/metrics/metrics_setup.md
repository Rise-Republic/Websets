# Metrics & Dashboarding Setup

## Overview
This guide describes exposing Prometheus metrics, provisioning Grafana dashboards, and enabling multi-tenancy and drill-down.

## Steps
1. Expose Prometheus metrics in all services (latency, error rate, volume, custom metrics).
2. Instrument Python/Node services with OpenTelemetry and export metrics via the Prometheus exporter.
3. Deploy Prometheus and Grafana via Helm. Mount `monitoring/prometheus/rules/key_metrics.yml` for alerting rules.
4. Create version-controlled Grafana dashboards (JSON/Terraform/Jsonnet). Example dashboard JSON lives in `monitoring/grafana/dashboards/websets_overview.json`.
5. Auto-provision dashboards per environment.
6. Enable multi-tenancy, time comparison, and drill-down.
7. Integrate trace IDs and SLO metrics into dashboards.
8. Import `monitoring/grafana/dashboards/websets_overview.json` into Grafana to see Websets metrics.

## Automation
- Terraform/Jsonnet for dashboard provisioning.
- CI/CD pipeline for metrics endpoint checks.
- Self-service dashboard templates.
