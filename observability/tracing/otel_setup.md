# Distributed Tracing Setup

## Overview
This guide describes how to implement distributed tracing across all services using OpenTelemetry, exporting traces to Tempo/Jaeger, and integrating with Grafana dashboards.

## Steps
1. Add OpenTelemetry SDKs to all Python, Node, and other services.
2. Enable auto-instrumentation for HTTP/gRPC endpoints, queue handlers, and storage APIs.
3. Add manual semantic span annotations for business logic and external calls (S3, DB).
4. Configure context propagation across all services and external systems.
5. Export traces to Tempo/Jaeger (Helm chart deployment).
6. Update structured logging to include trace IDs for trace-to-log correlation.
7. Create Grafana dashboards with trace drill-down.
8. Link trace views to SLO dashboards for root cause analysis.
9. Enable the OpenTelemetry Prometheus exporter for unified metrics and traces.

## Automation
- Use Helm charts for collector deployment.
- Add CI/CD pipeline step for auto-instrumentation validation.
- Provide self-service templates for new traces.
