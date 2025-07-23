# Alerting Rules Setup

## Overview
This guide covers Prometheus Alertmanager configuration, SLO/infra/security alerts, runbook links, routing, and deduplication.

## Steps
1. Define SLO-based, infra, and security alert rules in Prometheus.
2. Link alerts to runbooks.
3. Tag alerts with severity and route to PagerDuty/Slack by service ownership.
4. Enable deduplication and grouping in Alertmanager.
5. Version-control alert rules and runbooks. See `monitoring/prometheus/rules/key_metrics.yml` for sample rules.
6. Import `monitoring/grafana/dashboards/websets_overview.json` into Grafana for quick visibility on request volume and error rate.

## Automation
- Config-as-Code for alert rules (Helm/Terraform).
- CI/CD pipeline for alert rule validation.
- Peer review for alert changes.
