# Observability Infra Setup

This guide describes how to deploy the observability stack using Helm and Terraform in Kubernetes environments.

## Components

- OpenTelemetry Collector
- Tempo/Jaeger
- Prometheus
- Grafana
- ELK/OpenSearch
- Alertmanager

## Steps

1. Deploy OpenTelemetry Collector using Helm:
   - `helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts`
   - `helm install otel-collector open-telemetry/opentelemetry-collector -f observability/tracing/otel_collector_config.yaml`
2. Deploy Tempo/Jaeger for trace storage and visualization.
3. Deploy Prometheus and Grafana using Helm charts.
4. Deploy ELK/OpenSearch stack for centralized logging.
5. Deploy Alertmanager and configure with alert_rules.yml.
6. Use Terraform/Jsonnet for dashboard and alert provisioning.
7. Configure RBAC for all observability components.
8. Validate setup with integration tests and sample traces/logs/metrics.
