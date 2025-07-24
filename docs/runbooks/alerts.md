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

For credentials or access related alerts, see the [Secret Rotation guide](../SECRET_ROTATION.md).
