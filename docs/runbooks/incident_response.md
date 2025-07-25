# Incident Response Playbook

Follow this guide when escalating an incident affecting Websets.

1. **Detect** – Acknowledge alerts from PagerDuty or monitoring dashboards.
2. **Triage** – Collect symptoms, logs, and recent deploys to determine severity.
3. **Notify** – Post in the `#ops-incidents` Slack channel and create an incident ticket.
4. **Mitigate** – Roll back recent changes, apply hotfixes, or scale resources to restore service.
5. **Communicate** – Provide updates every 15 minutes until resolved and escalate to leadership for major outages.
6. **Postmortem** – Document the root cause, timeline, and remediation tasks in the incident ticket.
7. **Review** – Schedule a follow-up meeting to track long-term improvements.

See also [Secret Rotation Guide](../SECRET_ROTATION.md) for responding to compromised credentials.
