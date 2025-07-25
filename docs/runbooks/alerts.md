# Alert Response Playbook

This runbook describes standard procedures for handling common alerts.

## High Error Rate

1. Acknowledge the alert in PagerDuty.
2. Check recent deploys or configuration changes.
3. Inspect application logs for stack traces or failed requests.
4. If an incident is ongoing, escalate to the on-call engineer lead.

## Resource Exhaustion

1. Confirm the alert by checking Grafana dashboards.
2. Identify offending jobs or users consuming excessive resources.
3. Scale workers or throttle jobs as needed.
4. Document actions in the incident channel.

## Job Failure Rate

1. Inspect recent Celery task logs to identify common errors.
2. Check worker CPU and memory usage for spikes.
3. Retry or reschedule failed jobs after addressing the root cause.

## High Request Latency

1. Review recent deployments or spikes in traffic.
2. Check application logs for slow database queries or timeouts.
3. Verify infrastructure metrics for CPU or network saturation.

## SLO Error Budget Burn

1. Confirm burn rate in Grafana and Prometheus.
2. Identify failing components contributing to the burn.
3. Roll back recent changes or escalate if the trend continues.

See also [Secret Rotation Guide](../SECRET_ROTATION.md) for keeping credentials fresh.
