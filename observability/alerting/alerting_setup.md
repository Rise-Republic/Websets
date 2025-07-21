# Alerting Rules Setup

## Overview
This guide covers Prometheus Alertmanager configuration, SLO/infra/security alerts, runbook links, routing, and deduplication.

## Steps
1. Define SLO-based, infra, and security alert rules in Prometheus.
2. Link alerts to runbooks.
3. Tag alerts with severity and route to PagerDuty/Slack by service ownership.
4. Enable deduplication and grouping in Alertmanager.
5. Version-control alert rules and runbooks.

## Automation
- Config-as-Code for alert rules (Helm/Terraform).
- CI/CD pipeline for alert rule validation.
- Peer review for alert changes.
