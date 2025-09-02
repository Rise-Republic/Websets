# Monitoring & Observability Runbook

## Overview
This runbook covers monitoring, alerting, and observability procedures for the WebSets platform.

## Monitoring Stack

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Jaeger**: Distributed tracing
- **ELK Stack**: Log aggregation and analysis

### Architecture
```
Application → Prometheus → Grafana
           → AlertManager → PagerDuty/Slack
           → Jaeger (traces)
           → Elasticsearch (logs)
```

## Key Metrics

### Application Metrics
```prometheus
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database connections
db_connections_active
db_connections_idle

# Queue depth
celery_queue_length
```

### Infrastructure Metrics
```prometheus
# CPU usage
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)

# Network I/O
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])
```

### Business Metrics
```prometheus
# Dataset processing rate
rate(datasets_processed_total[5m])

# Search queries per second
rate(search_queries_total[5m])

# User registrations
rate(user_registrations_total[1h])

# Revenue metrics
sum(subscription_revenue_total)
```

## Alert Rules

### Critical Alerts (P0)
```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }}"

# Service down
- alert: ServiceDown
  expr: up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.instance }} is down"

# Database connection failure
- alert: DatabaseDown
  expr: db_connections_active == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Database connection lost"
```

### Warning Alerts (P1)
```yaml
# High response time
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High response time detected"
    description: "95th percentile response time is {{ $value }}s"

# High CPU usage
- alert: HighCPUUsage
  expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage on {{ $labels.instance }}"
    description: "CPU usage is {{ $value }}%"

# High memory usage
- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage on {{ $labels.instance }}"
    description: "Memory usage is {{ $value }}%"
```

## Dashboard Management

### Application Dashboard
```json
{
  "dashboard": {
    "title": "WebSets Application",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Infrastructure Dashboard
```json
{
  "dashboard": {
    "title": "WebSets Infrastructure",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{ instance }}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{ instance }}"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "targets": [
          {
            "expr": "100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)",
            "legendFormat": "{{ instance }} - {{ mountpoint }}"
          }
        ]
      }
    ]
  }
}
```

## Log Management

### Log Levels
- **ERROR**: System errors, exceptions
- **WARN**: Potential issues, degraded performance
- **INFO**: Normal operations, business events
- **DEBUG**: Detailed diagnostic information

### Log Format
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "websets-api",
  "version": "v1.2.3",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "user-789",
  "tenant_id": "tenant-123",
  "message": "Dataset processing completed",
  "metadata": {
    "dataset_id": 456,
    "processing_time_ms": 1500,
    "records_processed": 10000
  }
}
```

### Log Queries
```elasticsearch
# Error logs in last hour
level:ERROR AND @timestamp:[now-1h TO now]

# Slow queries
message:"slow query" AND processing_time_ms:>5000

# User activity
user_id:"user-123" AND @timestamp:[now-1d TO now]

# Failed authentication
message:"authentication failed" AND @timestamp:[now-1h TO now]
```

## Tracing

### Distributed Tracing Setup
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
```

### Trace Analysis
```bash
# Find slow traces
curl "http://jaeger:16686/api/traces?service=websets-api&limit=20&lookback=1h&minDuration=5s"

# Find error traces
curl "http://jaeger:16686/api/traces?service=websets-api&tags={\"error\":\"true\"}"

# Trace dependencies
curl "http://jaeger:16686/api/dependencies?endTs=$(date +%s)000&lookback=86400000"
```

## Health Checks

### Application Health Endpoints
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "unknown")
    }

@app.get("/health/db")
async def database_health():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "component": "database"}
    except Exception as e:
        return {"status": "unhealthy", "component": "database", "error": str(e)}

@app.get("/health/redis")
async def redis_health():
    try:
        redis_client.ping()
        return {"status": "healthy", "component": "redis"}
    except Exception as e:
        return {"status": "unhealthy", "component": "redis", "error": str(e)}
```

### Kubernetes Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

## Incident Response

### Alert Escalation
1. **P0 (Critical)**: Immediate PagerDuty alert
2. **P1 (High)**: Slack notification + email
3. **P2 (Medium)**: Email notification
4. **P3 (Low)**: Dashboard annotation

### Runbook Automation
```bash
# Auto-scaling on high CPU
kubectl autoscale deployment websets-production --cpu-percent=70 --min=3 --max=10

# Auto-restart on memory leak
kubectl set env deployment/websets-production MAX_MEMORY=1Gi
kubectl rollout restart deployment/websets-production
```

## Performance Monitoring

### SLA Targets
- **Availability**: 99.9% uptime
- **Response Time**: < 500ms (95th percentile)
- **Error Rate**: < 1%
- **Throughput**: > 1000 requests/second

### Performance Queries
```prometheus
# SLA compliance
(
  sum(rate(http_requests_total{status!~"5.."}[5m])) /
  sum(rate(http_requests_total[5m]))
) * 100

# Apdex score
(
  sum(rate(http_request_duration_seconds_bucket{le="0.5"}[5m])) +
  sum(rate(http_request_duration_seconds_bucket{le="2.0"}[5m])) / 2
) / sum(rate(http_request_duration_seconds_count[5m]))
```

## Capacity Planning

### Resource Utilization Trends
```prometheus
# CPU trend (7 days)
avg_over_time(
  100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
[7d:1h])

# Memory trend (7 days)
avg_over_time(
  (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
[7d:1h])

# Request volume trend (30 days)
avg_over_time(sum(rate(http_requests_total[5m]))[30d:1h])
```

### Scaling Recommendations
```bash
# Horizontal Pod Autoscaler
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: websets-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: websets-production
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

## Troubleshooting Guide

### High Error Rate
1. Check application logs for exceptions
2. Verify database connectivity
3. Check external service dependencies
4. Review recent deployments
5. Scale up if resource constrained

### High Response Time
1. Check database query performance
2. Review cache hit rates
3. Analyze slow traces in Jaeger
4. Check resource utilization
5. Consider horizontal scaling

### Memory Leaks
1. Monitor heap usage over time
2. Generate heap dumps
3. Analyze with profiling tools
4. Review recent code changes
5. Restart affected pods

### Database Issues
1. Check connection pool status
2. Review slow query logs
3. Monitor database metrics
4. Check for lock contention
5. Verify backup status

## Maintenance Procedures

### Weekly Tasks
- [ ] Review dashboard metrics
- [ ] Check alert noise levels
- [ ] Update capacity forecasts
- [ ] Review incident reports
- [ ] Clean up old logs and metrics

### Monthly Tasks
- [ ] Capacity planning review
- [ ] SLA compliance report
- [ ] Dashboard optimization
- [ ] Alert rule tuning
- [ ] Performance baseline update

### Quarterly Tasks
- [ ] Monitoring stack upgrade
- [ ] Retention policy review
- [ ] Cost optimization analysis
- [ ] Disaster recovery testing
- [ ] Observability strategy review
