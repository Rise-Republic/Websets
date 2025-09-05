# WebSets Operations Runbook

## Build, Release, Rollback & On-Call Commands

This runbook provides essential commands and procedures for operating the WebSets platform in production.

## 🏗️ Build Operations

### Local Development Build
```bash
# Full local build and test
docker-compose -f deploy/docker-compose/docker-compose.yml build
docker-compose -f deploy/docker-compose/docker-compose.yml up -d

# Verify services are healthy
curl -f http://localhost:8000/health
curl -f http://localhost:3000
```

### CI/CD Build Triggers
```bash
# Trigger build for specific service
gh workflow run build-test-deploy.yml \
  --field services="api-gateway" \
  --field environment="staging"

# Trigger full build for all services
gh workflow run build-test-deploy.yml \
  --field services="all" \
  --field environment="prod"

# Check build status
gh run list --workflow=build-test-deploy.yml --limit=5
```

### Manual Container Build
```bash
# Build specific service
docker build -t ghcr.io/rise-republic/websets-api-gateway:latest \
  -f services/api-gateway/Dockerfile .

# Build with security scanning
docker build -t temp-scan services/api-gateway/
trivy image --exit-code 1 temp-scan
```

## 🚀 Release Operations

### Semantic Release (Automated)
```bash
# Check current version
git describe --tags --abbrev=0

# Create release branch
git checkout -b release/v1.2.3
git push origin release/v1.2.3

# Automated release will trigger on merge to main
# Monitor release workflow
gh run watch --workflow=semantic-release.yml
```

### Manual Release Process
```bash
# Tag release
git tag -a v1.2.3 -m "Release v1.2.3: Feature improvements and security updates"
git push origin v1.2.3

# Trigger production deployment
gh workflow run production-deploy.yml \
  --field version="v1.2.3" \
  --field environment="production" \
  --field deployment_strategy="blue-green"

# Monitor deployment
gh run watch --workflow=production-deploy.yml
```

### Release Validation
```bash
# Verify release artifacts
gh release view v1.2.3

# Check container images
docker manifest inspect ghcr.io/rise-republic/websets-api-gateway:v1.2.3

# Validate SBOM and signatures
cosign verify ghcr.io/rise-republic/websets-api-gateway:v1.2.3
cosign download sbom ghcr.io/rise-republic/websets-api-gateway:v1.2.3
```

## 🔄 Rollback Operations

### Emergency Rollback
```bash
# Immediate rollback to previous version
gh workflow run rollback.yml \
  --field target_version="v1.2.2" \
  --field environment="production" \
  --field rollback_reason="Critical bug" \
  --field skip_verification="false"

# Emergency rollback (skip verification)
gh workflow run rollback.yml \
  --field target_version="v1.2.2" \
  --field environment="production" \
  --field rollback_reason="Service unavailable" \
  --field skip_verification="true"
```

### Database Rollback
```bash
# Check migration history
cd db/
alembic history

# Rollback to specific migration
alembic downgrade <revision_id>

# Rollback one migration
alembic downgrade -1
```

### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/websets-api-gateway -n websets-prod

# Rollback to specific revision
kubectl rollout undo deployment/websets-api-gateway --to-revision=2 -n websets-prod

# Check rollout status
kubectl rollout status deployment/websets-api-gateway -n websets-prod
```

## 📊 Monitoring & Health Checks

### Service Health Checks
```bash
# Production health checks
curl -f https://api.websets.com/health
curl -f https://websets.com/health

# Staging health checks
curl -f https://staging-api.websets.com/health
curl -f https://staging.websets.com/health

# Internal service checks
kubectl get pods -n websets-prod
kubectl get svc -n websets-prod
```

### Performance Monitoring
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.websets.com/health

# Load testing
k6 run tests/performance/load-test.js

# Database performance
kubectl exec -it postgres-0 -n websets-prod -- psql -U postgres -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;"
```

### Log Analysis
```bash
# Application logs
kubectl logs -f deployment/websets-api-gateway -n websets-prod

# Error log analysis
kubectl logs deployment/websets-api-gateway -n websets-prod | grep ERROR

# Audit logs
kubectl logs deployment/websets-api-gateway -n websets-prod | grep AUDIT
```

## 🚨 Incident Response

### Severity Levels
- **P0 (Critical)**: Service completely down, data loss, security breach
- **P1 (High)**: Major functionality broken, significant user impact
- **P2 (Medium)**: Minor functionality issues, limited user impact
- **P3 (Low)**: Cosmetic issues, no user impact

### P0 Incident Response
```bash
# 1. Immediate assessment
curl -f https://api.websets.com/health
kubectl get pods -n websets-prod
kubectl get events -n websets-prod --sort-by='.lastTimestamp'

# 2. Emergency rollback if needed
gh workflow run rollback.yml \
  --field target_version="<last_known_good>" \
  --field environment="production" \
  --field rollback_reason="P0 incident" \
  --field skip_verification="true"

# 3. Scale resources if needed
kubectl scale deployment websets-api-gateway --replicas=5 -n websets-prod

# 4. Check dependencies
kubectl get pods -n websets-prod | grep -E "(postgres|redis|qdrant)"
```

### Incident Communication
```bash
# Update status page
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth TOKEN" \
  -d '{"incident": {"name": "Service Degradation", "status": "investigating"}}'

# Slack notification
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🚨 P0 Incident: Service down - investigating"}' \
  $SLACK_WEBHOOK_URL
```

## 🔧 Maintenance Operations

### Scheduled Maintenance
```bash
# Put service in maintenance mode
kubectl patch ingress websets-ingress -n websets-prod \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/default-backend":"maintenance-page"}}}'

# Database maintenance
kubectl exec -it postgres-0 -n websets-prod -- psql -U postgres -c "
VACUUM ANALYZE;
REINDEX DATABASE websets;"

# Clear maintenance mode
kubectl patch ingress websets-ingress -n websets-prod \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/default-backend":null}}}'
```

### Certificate Renewal
```bash
# Check certificate expiry
kubectl get certificates -n websets-prod
kubectl describe certificate websets-tls -n websets-prod

# Force certificate renewal
kubectl delete certificate websets-tls -n websets-prod
kubectl apply -f deploy/helm/websets/templates/certificate.yaml
```

### Backup Operations
```bash
# Database backup
kubectl exec postgres-0 -n websets-prod -- pg_dump -U postgres websets > backup-$(date +%Y%m%d).sql

# Verify backup
kubectl exec postgres-0 -n websets-prod -- pg_restore --list backup-$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql s3://websets-backups/$(date +%Y/%m/%d)/
```

## 🔍 Debugging Commands

### Container Debugging
```bash
# Debug pod issues
kubectl describe pod <pod-name> -n websets-prod
kubectl logs <pod-name> -n websets-prod --previous

# Execute into container
kubectl exec -it <pod-name> -n websets-prod -- /bin/bash

# Port forward for local debugging
kubectl port-forward svc/websets-api-gateway 8000:8000 -n websets-prod
```

### Network Debugging
```bash
# Test service connectivity
kubectl run debug --image=nicolaka/netshoot -it --rm -n websets-prod
# Inside debug pod:
nslookup websets-api-gateway
curl -v http://websets-api-gateway:8000/health

# Check ingress
kubectl get ingress -n websets-prod
kubectl describe ingress websets-ingress -n websets-prod
```

### Database Debugging
```bash
# Check database connections
kubectl exec postgres-0 -n websets-prod -- psql -U postgres -c "
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity WHERE state = 'active';"

# Check slow queries
kubectl exec postgres-0 -n websets-prod -- psql -U postgres -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"
```

## 📱 On-Call Procedures

### Alert Response
```bash
# Check alert details
curl -s http://alertmanager.websets.com/api/v1/alerts | jq '.'

# Silence alert (1 hour)
curl -X POST http://alertmanager.websets.com/api/v1/silences \
  -d '{"matchers":[{"name":"alertname","value":"HighErrorRate"}],"startsAt":"2023-01-01T00:00:00Z","endsAt":"2023-01-01T01:00:00Z","comment":"Investigating issue"}'

# Check Grafana dashboards
open https://grafana.websets.com/d/websets-overview
```

### Escalation Procedures
1. **L1 Response** (0-15 min): Initial assessment and basic troubleshooting
2. **L2 Escalation** (15-30 min): Advanced debugging and potential rollback
3. **L3 Escalation** (30+ min): Engineering team involvement
4. **Executive Escalation**: For P0 incidents lasting >1 hour

### Contact Information
- **On-call Engineer**: Check PagerDuty schedule
- **Engineering Manager**: Slack @eng-manager
- **Platform Team**: Slack #platform-team
- **Security Team**: Slack #security-incidents

## 📋 Checklists

### Pre-deployment Checklist
- [ ] All CI checks passing
- [ ] Security scans clean
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Stakeholders notified

### Post-deployment Checklist
- [ ] Health checks passing
- [ ] Performance metrics normal
- [ ] Error rates within SLA
- [ ] User acceptance testing passed
- [ ] Monitoring dashboards updated
- [ ] Documentation updated

### Incident Response Checklist
- [ ] Incident severity assessed
- [ ] Stakeholders notified
- [ ] Status page updated
- [ ] Mitigation actions taken
- [ ] Root cause identified
- [ ] Post-mortem scheduled
- [ ] Prevention measures implemented

---

**Emergency Contact**: +1-555-WEBSETS (24/7 on-call support)  
**Status Page**: https://status.websets.com  
**Runbook Updates**: Create PR against `docs/ops-runbook.md`
