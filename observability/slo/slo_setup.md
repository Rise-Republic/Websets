# SLO/SLI Governance Setup

## Overview
This guide describes SLI definitions, SLO dashboards, error budget, burn rate, and catalog publishing.

## Steps
1. Define SLIs: availability, latency, error rate, throughput.
2. Document SLI formulas (e.g., `(successful_requests / total_requests) * 100`).
3. Set SLOs per business tier (e.g., Tier 1 = 99.99%).
4. Create dashboards for burn rate, error budget, real-time alerts.
5. Integrate SLO reviews into engineering retrospectives.
6. Publish SLOs in Backstage/service catalog.

## Automation
- Self-service SLO templates.
- Config-as-Code for SLO definitions.
- CI/CD checks for SLO compliance.

## Webset Miner Example
- The file `observability/slo/websets_slo.json` contains the SLO definition for the `webset-miner` service.
- Prometheus recording rules in `monitoring/prometheus/rules/slo_recording_rules.yml` generate `slo_*` metrics.
- Grafana dashboard JSON lives in `monitoring/grafana/dashboards/websets_slo.json` and visualizes availability, latency, and burn rate.
