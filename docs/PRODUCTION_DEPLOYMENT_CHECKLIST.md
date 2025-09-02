# Production Deployment Checklist

## Pre-Deployment Checklist

### Code Quality & Testing
- [ ] All tests passing in CI pipeline
- [ ] Code coverage ≥80% for unit tests
- [ ] Integration tests completed successfully
- [ ] Contract tests validated (Pact)
- [ ] Performance tests meet SLA requirements
- [ ] Accessibility tests passing (WCAG 2.1 AA)
- [ ] Security scans completed (SAST, DAST, dependencies)
- [ ] No critical or high severity vulnerabilities

### Infrastructure & Environment
- [ ] Production environment health verified
- [ ] Database migrations tested and ready
- [ ] Kubernetes cluster resources available
- [ ] Container images built and signed
- [ ] Secrets and configuration updated
- [ ] Monitoring and alerting configured
- [ ] Backup systems verified

### Documentation & Communication
- [ ] Release notes prepared
- [ ] Deployment plan reviewed
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Support team briefed
- [ ] Change management approval obtained

## Deployment Execution

### Phase 1: Pre-Deployment Validation
- [ ] Verify target version exists and is signed
- [ ] Run pre-deployment security scan
- [ ] Check performance baseline
- [ ] Validate database migration compatibility
- [ ] Confirm backup completion

### Phase 2: Blue-Green Deployment
- [ ] Deploy to inactive environment (blue/green)
- [ ] Wait for deployment completion
- [ ] Run health checks on new deployment
- [ ] Execute smoke tests
- [ ] Validate application functionality
- [ ] Check database connectivity
- [ ] Verify external service integrations

### Phase 3: Traffic Switch
- [ ] Switch load balancer to new environment
- [ ] Monitor error rates and response times
- [ ] Validate user authentication flows
- [ ] Check critical business functions
- [ ] Monitor for 10 minutes minimum
- [ ] Confirm all services healthy

### Phase 4: Post-Deployment Validation
- [ ] Run full smoke test suite
- [ ] Verify monitoring dashboards
- [ ] Check alert configurations
- [ ] Validate log aggregation
- [ ] Test rollback procedures (if safe)
- [ ] Update deployment documentation

## Rollback Procedures

### Immediate Rollback Triggers
- [ ] Error rate > 5% for 2+ minutes
- [ ] Response time > 5 seconds (95th percentile)
- [ ] Critical functionality broken
- [ ] Database connectivity issues
- [ ] Security incident detected

### Rollback Execution
- [ ] Trigger emergency rollback workflow
- [ ] Switch traffic back to previous environment
- [ ] Verify system stability
- [ ] Run health checks
- [ ] Monitor for 15 minutes
- [ ] Document rollback reason
- [ ] Notify stakeholders
- [ ] Schedule post-mortem

## Post-Deployment Tasks

### Immediate (0-2 hours)
- [ ] Monitor system metrics
- [ ] Check error logs
- [ ] Validate user reports
- [ ] Update status page
- [ ] Notify success to stakeholders
- [ ] Document any issues encountered

### Short-term (2-24 hours)
- [ ] Review performance metrics
- [ ] Analyze user behavior changes
- [ ] Check business KPIs
- [ ] Validate backup systems
- [ ] Update capacity planning data
- [ ] Schedule team retrospective

### Long-term (1-7 days)
- [ ] Conduct deployment retrospective
- [ ] Update runbooks based on learnings
- [ ] Review and tune alert thresholds
- [ ] Analyze cost impact
- [ ] Plan next deployment improvements
- [ ] Update disaster recovery procedures

## Emergency Contacts

### Primary On-Call
- **Platform Team**: @platform-oncall
- **Engineering Manager**: @eng-manager
- **DevOps Lead**: @devops-lead

### Secondary Contacts
- **Security Team**: @security-team
- **Database Team**: @database-team
- **Product Manager**: @product-manager

### Escalation Matrix
1. **P0 (Critical)**: Immediate escalation to platform team
2. **P1 (High)**: Escalate within 15 minutes
3. **P2 (Medium)**: Escalate within 1 hour

## Key Metrics to Monitor

### Application Metrics
- Request rate (baseline: 1000+ req/sec)
- Error rate (target: <1%)
- Response time (target: <500ms p95)
- Database connections (monitor pool usage)
- Cache hit rate (target: >80%)

### Infrastructure Metrics
- CPU usage (alert: >80%)
- Memory usage (alert: >85%)
- Disk usage (alert: >90%)
- Network I/O
- Pod restart count

### Business Metrics
- User registrations
- Dataset processing rate
- Search query volume
- Revenue impact
- Customer satisfaction

## Dashboard URLs

### Production Monitoring
- **Application Dashboard**: https://grafana.websets.com/d/websets-app
- **Infrastructure Dashboard**: https://grafana.websets.com/d/websets-infra
- **Business Dashboard**: https://grafana.websets.com/d/websets-business

### Status Pages
- **Internal Status**: https://status.internal.websets.com
- **Public Status**: https://status.websets.com
- **Incident Management**: https://incidents.websets.com

## Deployment Approval

### Required Approvals
- [ ] Engineering Manager
- [ ] DevOps Lead
- [ ] Security Team (for security-related changes)
- [ ] Product Manager (for feature releases)

### Sign-off
- **Deployment Lead**: _________________ Date: _________
- **Engineering Manager**: _____________ Date: _________
- **DevOps Lead**: ____________________ Date: _________

---

**Note**: This checklist must be completed for every production deployment. Keep a copy of the completed checklist for audit and retrospective purposes.
