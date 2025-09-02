# Deployment Runbook

## Overview
This runbook provides step-by-step procedures for deploying the WebSets application across different environments.

## Pre-Deployment Checklist

### Prerequisites
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scans completed successfully
- [ ] Performance benchmarks met
- [ ] Database migrations reviewed and tested
- [ ] Feature flags configured appropriately
- [ ] Monitoring and alerting configured
- [ ] Rollback plan prepared

### Environment Verification
```bash
# Verify environment health
kubectl get nodes
kubectl get pods -n websets-system
kubectl top nodes

# Check resource availability
kubectl describe nodes | grep -A 5 "Allocated resources"

# Verify database connectivity
kubectl exec -it deployment/websets-production -- python -c "
from app.database import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection: OK')
"
```

## Deployment Procedures

### 1. Staging Deployment

#### Automated Staging Deployment
```bash
# Trigger via GitHub Actions
gh workflow run semantic-release.yml

# Monitor deployment
kubectl rollout status deployment/websets-staging -n staging
```

#### Manual Staging Deployment
```bash
# Set environment variables
export VERSION="v1.2.3"
export ENVIRONMENT="staging"

# Update deployment manifest
sed -i "s|image: .*|image: ghcr.io/websets/websets:${VERSION}|" k8s/deployment-staging.yaml

# Apply deployment
kubectl apply -f k8s/deployment-staging.yaml
kubectl apply -f k8s/service.yaml

# Wait for rollout
kubectl rollout status deployment/websets-staging --timeout=600s

# Verify deployment
curl -f https://staging.websets.example.com/health
```

#### Staging Verification
```bash
# Health checks
curl -f https://staging.websets.example.com/health
curl -f https://staging.websets.example.com/health/db
curl -f https://staging.websets.example.com/health/redis

# Smoke tests
pytest tests/smoke/ --base-url=https://staging.websets.example.com

# Performance verification
k6 run tests/performance/k6_smoke.js --env BASE_URL=https://staging.websets.example.com
```

### 2. Production Deployment

#### Blue-Green Deployment (Recommended)
```bash
# Trigger production deployment
gh workflow run production-deploy.yml \
  -f version=v1.2.3 \
  -f environment=production \
  -f deployment_strategy=blue-green

# Monitor deployment progress
gh run list --workflow=production-deploy.yml --limit=1
gh run watch <run-id>
```

#### Manual Blue-Green Deployment
```bash
# Step 1: Determine current environment
CURRENT_ENV=$(kubectl get service websets-production -o jsonpath='{.spec.selector.version}')
TARGET_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

echo "Current: $CURRENT_ENV, Target: $TARGET_ENV"

# Step 2: Deploy to target environment
export VERSION="v1.2.3"
sed -i "s|image: .*|image: ghcr.io/websets/websets:${VERSION}|" k8s/deployment-${TARGET_ENV}.yaml
kubectl apply -f k8s/deployment-${TARGET_ENV}.yaml

# Step 3: Wait for deployment
kubectl rollout status deployment/websets-${TARGET_ENV} --timeout=600s

# Step 4: Health check target environment
TARGET_URL="https://${TARGET_ENV}.websets.example.com"
for i in {1..10}; do
  if curl -f "$TARGET_URL/health"; then
    echo "Health check passed"
    break
  fi
  sleep 10
done

# Step 5: Run smoke tests
pytest tests/smoke/ --base-url="$TARGET_URL"

# Step 6: Switch traffic
kubectl patch service websets-production -p "{\"spec\":{\"selector\":{\"version\":\"${TARGET_ENV}\"}}}"

# Step 7: Verify traffic switch
sleep 10
curl -f "https://websets.example.com/health"

# Step 8: Monitor for 5 minutes
for i in {1..30}; do
  if ! curl -f "https://websets.example.com/health"; then
    echo "Health check failed - consider rollback"
    exit 1
  fi
  sleep 10
done
```

#### Rolling Deployment
```bash
# Update deployment image
kubectl set image deployment/websets-production \
  websets=ghcr.io/websets/websets:v1.2.3

# Monitor rollout
kubectl rollout status deployment/websets-production --timeout=600s

# Verify deployment
kubectl get pods -l app=websets-production
curl -f "https://websets.example.com/health"
```

### 3. Database Migrations

#### Pre-Migration Checks
```bash
# Backup database
kubectl exec -it deployment/postgres -- pg_dump websets > backup-$(date +%Y%m%d-%H%M%S).sql

# Verify migration scripts
alembic check
alembic history
alembic show head
```

#### Migration Execution
```bash
# Run migrations
kubectl exec -it deployment/websets-production -- alembic upgrade head

# Verify migration
kubectl exec -it deployment/websets-production -- alembic current
```

#### Migration Rollback
```bash
# Rollback to previous version
kubectl exec -it deployment/websets-production -- alembic downgrade -1

# Restore from backup if needed
kubectl exec -i deployment/postgres -- psql websets < backup-20240101-120000.sql
```

## Post-Deployment Verification

### Health Checks
```bash
# Application health
curl -f https://websets.example.com/health

# Database connectivity
curl -f https://websets.example.com/health/db

# External dependencies
curl -f https://websets.example.com/health/redis
curl -f https://websets.example.com/health/s3
```

### Functional Testing
```bash
# API endpoints
curl -f https://websets.example.com/v1/datasets \
  -H "Authorization: Bearer $TEST_TOKEN"

# Authentication flow
curl -f https://websets.example.com/auth/login

# Search functionality
curl -f https://websets.example.com/v1/search \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Performance Verification
```bash
# Response time check
response_time=$(curl -o /dev/null -s -w '%{time_total}' https://websets.example.com/health)
if (( $(echo "$response_time > 2.0" | bc -l) )); then
  echo "WARNING: Response time too high: ${response_time}s"
fi

# Load test
k6 run tests/performance/k6_performance.js --env BASE_URL=https://websets.example.com
```

### Monitoring Verification
```bash
# Check metrics collection
curl -f https://websets.example.com/metrics

# Verify Prometheus targets
curl -f http://prometheus:9090/api/v1/targets

# Check Grafana dashboards
curl -f http://grafana:3000/api/health
```

## Rollback Procedures

### Automated Rollback
```bash
# Trigger emergency rollback
gh workflow run rollback.yml \
  -f target_version=v1.2.2 \
  -f environment=production \
  -f rollback_reason="Critical bug"
```

### Manual Rollback
```bash
# Quick rollback using kubectl
kubectl rollout undo deployment/websets-production

# Rollback to specific version
kubectl rollout undo deployment/websets-production --to-revision=2

# Verify rollback
kubectl rollout status deployment/websets-production
curl -f https://websets.example.com/health
```

### Blue-Green Rollback
```bash
# Switch back to previous environment
CURRENT_ENV=$(kubectl get service websets-production -o jsonpath='{.spec.selector.version}')
PREVIOUS_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

kubectl patch service websets-production -p "{\"spec\":{\"selector\":{\"version\":\"${PREVIOUS_ENV}\"}}}"

# Verify rollback
curl -f https://websets.example.com/health
```

## Troubleshooting

### Common Issues

#### Deployment Stuck
```bash
# Check pod status
kubectl get pods -l app=websets-production

# Describe problematic pods
kubectl describe pod <pod-name>

# Check logs
kubectl logs -f deployment/websets-production

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

#### Health Check Failures
```bash
# Check application logs
kubectl logs -f deployment/websets-production --tail=100

# Check database connectivity
kubectl exec -it deployment/websets-production -- python -c "
from app.database import engine
engine.connect()
"

# Check external dependencies
kubectl exec -it deployment/websets-production -- curl -f http://redis:6379/ping
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -l app=websets-production
kubectl describe nodes

# Check database performance
kubectl exec -it deployment/postgres -- psql websets -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

### Emergency Contacts

- **On-Call Engineer**: @oncall
- **Platform Team**: @platform-team  
- **Database Team**: @database-team
- **Security Team**: @security-team
- **Engineering Manager**: @eng-manager

### Escalation Matrix

1. **P0 (Critical)**: Immediate escalation to on-call engineer
2. **P1 (High)**: Escalate within 15 minutes
3. **P2 (Medium)**: Escalate within 1 hour
4. **P3 (Low)**: Escalate within 4 hours

## Monitoring and Alerting

### Key Metrics to Monitor
- Response time (< 500ms p95)
- Error rate (< 1%)
- Throughput (requests/second)
- Database connections
- Memory usage (< 80%)
- CPU usage (< 70%)

### Alert Thresholds
- **Critical**: Error rate > 5%, Response time > 2s
- **Warning**: Error rate > 1%, Response time > 1s
- **Info**: Deployment events, scaling events

### Dashboard URLs
- **Application Dashboard**: http://grafana:3000/d/websets-app
- **Infrastructure Dashboard**: http://grafana:3000/d/websets-infra
- **Database Dashboard**: http://grafana:3000/d/websets-db

## Documentation Updates

After each deployment:
- [ ] Update CHANGELOG.md
- [ ] Update deployment notes
- [ ] Document any issues encountered
- [ ] Update runbook if procedures changed
- [ ] Notify stakeholders of completion
