# Monitoring and Rollback Plan

WebSet Miner exposes Prometheus metrics and includes alerting rules under `monitoring/prometheus/rules/`. Dashboards are provisioned from the JSON files in `monitoring/grafana/dashboards/`.

## Monitoring Checklist
1. Deploy Prometheus and Grafana as described in `observability/metrics/metrics_setup.md`.
2. Import the dashboards in the `monitoring/grafana/dashboards` directory.
3. Configure Alertmanager with the rules from `monitoring/prometheus/rules/key_metrics.yml` and `slo_recording_rules.yml`.
4. Review alerts using the runbooks in `docs/runbooks/`.

## Rollback Procedure
1. If a deployment causes instability, execute the blue/green script to switch back to the previous version:
   ```bash
   scripts/blue_green_deploy.sh <blue|green>
   ```
2. Verify service health via `kubectl rollout status` and Grafana dashboards.
3. Document the incident using `docs/runbooks/incident_response.md` and restore from backups if needed following `docs/runbooks/backups.md`.

## Automated Rollback Triggers

The deployment workflow performs a post-deploy health check against Prometheus.
If the 95th percentile latency exceeds **1 second** or the HTTP error rate is
above **5%**, the workflow runs:

```bash
scripts/blue_green_deploy.sh <previous_color>
```

The previous color is derived from the current `webset-miner` service selector
so traffic routes back to the last stable deployment.
