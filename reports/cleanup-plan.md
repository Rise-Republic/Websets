# Enterprise Cleanup Implementation Plan

## Phase 2: Detailed Cleanup Plan

Based on the comprehensive audit findings, this plan outlines specific changes to reorganize the WebSets repository into an enterprise-grade structure.

## Directory Reorganization Commands

### 1. Service Structure Migration

```bash
# Create new directory structure
mkdir -p apps/web-ui
mkdir -p services/api-gateway/src
mkdir -p services/worker-celery/src
mkdir -p packages/python-common
mkdir -p packages/typescript-common
mkdir -p db/migrations
mkdir -p db/seeds
mkdir -p deploy/helm/websets/{templates,values}
mkdir -p deploy/docker-compose
mkdir -p scripts/{dev,ci,ops}
mkdir -p tools/{linting,security}
mkdir -p docs/{architecture,runbooks,api,development}
mkdir -p .attic/$(date +%Y-%m-%d)

# Move backend application
git mv app/ services/api-gateway/src/app/
git mv requirements.txt services/api-gateway/
git mv requirements-dev.txt services/api-gateway/

# Move frontend application  
git mv src/ apps/web-ui/src/
git mv package.json apps/web-ui/
git mv package-lock.json apps/web-ui/
git mv index.html apps/web-ui/
git mv vite.config.ts apps/web-ui/
git mv tsconfig*.json apps/web-ui/
git mv postcss.config.js apps/web-ui/
git mv tailwind.config.js apps/web-ui/
git mv eslint.config.js apps/web-ui/
git mv jest.config.js apps/web-ui/

# Move database assets
git mv migrations/ db/migrations/
git mv alembic.ini db/

# Move deployment configurations
git mv k8s/ deploy/helm/websets/templates/
git mv docker-compose.yml deploy/docker-compose/
git mv docker-compose.monitoring.yml deploy/docker-compose/

# Move infrastructure
git mv infra/terraform/ infra/terraform/environments/
mkdir -p infra/terraform/modules

# Reorganize scripts
git mv scripts/dev_* scripts/dev/
git mv scripts/ci_* scripts/ci/
git mv scripts/ops_* scripts/ops/

# Move documentation
git mv docs/runbooks/ docs/runbooks/
git mv docs/adr/ docs/architecture/
git mv API_REFERENCE.md docs/api/
```

### 2. Configuration Standardization

| Change | Rationale | Risk | Rollback |
|--------|-----------|------|----------|
| Move `app/` → `services/api-gateway/src/app/` | Service-centric organization | Medium - import path updates needed | `git mv services/api-gateway/src/app/ app/` |
| Move `src/` → `apps/web-ui/src/` | Separate frontend application | Low - build config updates only | `git mv apps/web-ui/src/ src/` |
| Consolidate workflows | Reduce duplication, improve maintainability | Low - additive changes | Revert individual workflow files |
| Create .dockerignore | Security and performance improvement | None - additive only | `git rm .dockerignore` |
| Add HEALTHCHECK | Container orchestration improvement | None - additive only | Remove HEALTHCHECK line |

## File Creation Plan

### 1. Missing .dockerignore
```dockerfile
# .dockerignore
node_modules/
.git/
__pycache__/
.pytest_cache/
*.pyc
.coverage
.env*
.vscode/
.idea/
*.log
dist/
build/
reports/
.attic/
.next/
coverage/
target/
.terraform/
*.tfstate*
.DS_Store
Thumbs.db
```

### 2. Enhanced Dockerfile
```dockerfile
# Dockerfile (updated)
# syntax=docker/dockerfile:1

########## Frontend build stage ##########
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY apps/web-ui/package*.json ./
RUN npm ci --only=production
COPY apps/web-ui/ ./
RUN npm run build

########## Backend build stage ##########
FROM python:3.13-slim AS backend-build
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/api-gateway/requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix /install --no-cache-dir -r requirements.txt

########## Final runtime stage ##########
FROM gcr.io/distroless/python3-debian12 AS runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=backend-build /install /usr/local
COPY --from=backend-build --chown=65534:65534 /app /app
COPY services/api-gateway/src/app ./app
COPY db/migrations ./migrations
COPY db/alembic.ini .
COPY --from=frontend-build /frontend/dist ./static
EXPOSE 8000
USER 65534
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Helm Chart Structure
```yaml
# deploy/helm/websets/Chart.yaml
apiVersion: v2
name: websets
description: WebSets Multi-tenant B2B SaaS Platform
type: application
version: 0.1.0
appVersion: "1.0.0"

# deploy/helm/websets/values/values-prod.yaml
global:
  environment: production
  registry: ghcr.io/rise-republic
  imageTag: v1.2.3

services:
  api-gateway:
    enabled: true
    replicas: 3
    image:
      repository: websets-api
      tag: ""  # Uses global.imageTag
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
    
  web-ui:
    enabled: true
    replicas: 2
    image:
      repository: websets-web
      tag: ""
    
security:
  runAsNonRoot: true
  runAsUser: 65534
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### 4. Consolidated CI Workflows

#### Reusable Security Action
```yaml
# .github/actions/security-scan/action.yml
name: Comprehensive Security Scan
description: Unified security scanning for all services
inputs:
  service-path:
    description: Path to service directory
    required: true
  scan-types:
    description: Comma-separated scan types (sast,dast,container,deps)
    required: false
    default: "sast,container,deps"

runs:
  using: composite
  steps:
    - name: SAST Scanning
      if: contains(inputs.scan-types, 'sast')
      shell: bash
      run: |
        semgrep --config=auto ${{ inputs.service-path }}
        bandit -r ${{ inputs.service-path }} -f json || true
    
    - name: Container Scanning  
      if: contains(inputs.scan-types, 'container')
      shell: bash
      run: |
        docker build -t temp-scan ${{ inputs.service-path }}
        trivy image --exit-code 1 temp-scan
        
    - name: Dependency Scanning
      if: contains(inputs.scan-types, 'deps')
      shell: bash
      run: |
        safety check -r ${{ inputs.service-path }}/requirements.txt
        npm audit --prefix ${{ inputs.service-path }}
```

#### Unified Build Workflow
```yaml
# .github/workflows/build-test-deploy.yml
name: Build Test Deploy
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, web-ui, worker-celery]
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/security-scan
        with:
          service-path: services/${{ matrix.service }}
          
  build:
    needs: security
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, web-ui]
        environment: [dev, staging, prod]
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/build-service
        with:
          service: ${{ matrix.service }}
          environment: ${{ matrix.environment }}
```

## Import Path Updates

### Python Import Changes
```python
# Update all Python imports
# From: from app.models import User
# To: from services.api_gateway.src.app.models import User

# Automated with sed/awk
find services/api-gateway -name "*.py" -exec sed -i 's/from app\./from services.api_gateway.src.app./g' {} \;
find services/api-gateway -name "*.py" -exec sed -i 's/import app\./import services.api_gateway.src.app./g' {} \;
```

### TypeScript Import Changes  
```typescript
// Update TypeScript imports
// From: import { Component } from '../components'
// To: import { Component } from '../components'  (relative paths unchanged)

// Update absolute imports in build configs
// vite.config.ts, tsconfig.json path mappings
```

### Docker Context Updates
```dockerfile
# Update COPY commands in Dockerfile
# From: COPY app ./app
# To: COPY services/api-gateway/src/app ./app
```

## Workflow Consolidation Plan

### Remove Redundant Workflows
```bash
# Safe to remove (functionality covered elsewhere)
git rm .github/workflows/security.yml          # Covered by security-enhanced.yml
git rm .github/workflows/security-scan.yml     # Minimal, merge into comprehensive
git rm .github/workflows/ci.yml                # Covered by test.yml
git rm .github/workflows/build-publish.yml     # Merge into unified build

# Move to attic (contested/unclear)
git mv .github/workflows/monthly-format.yml .attic/$(date +%Y-%m-%d)/
git mv .github/workflows/grafana-drift.yml .attic/$(date +%Y-%m-%d)/
```

### Create Unified Workflows
```bash
# Consolidate security workflows
cat .github/workflows/security-enhanced.yml .github/workflows/snyk-security.yml > .github/workflows/security-comprehensive.yml

# Create reusable actions
mkdir -p .github/actions/{security-scan,build-service,setup-dependencies}
```

## Environment Configuration Consolidation

### Centralized Environment Variables
```yaml
# deploy/helm/websets/values/values-base.yaml (shared config)
database:
  host: postgres
  port: 5432
  name: websets

redis:
  host: redis
  port: 6379

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

### Environment-Specific Overrides
```yaml
# deploy/helm/websets/values/values-prod.yaml
database:
  host: prod-postgres.internal
  ssl: true
  
security:
  networkPolicies:
    enabled: true
  podSecurityPolicy:
    enabled: true
```

## Validation Steps

### Pre-Change Validation
```bash
# Ensure all tests pass
python -m pytest tests/
npm test

# Validate current Docker build
docker build -t websets:current .

# Check current K8s manifests
kubectl apply --dry-run=client -f k8s/

# Validate Terraform
terraform -chdir=infra/terraform validate
```

### Post-Change Validation  
```bash
# Test new structure builds
docker build -t websets:new .

# Validate Helm charts
helm lint deploy/helm/websets/
helm template deploy/helm/websets/ --values deploy/helm/websets/values/values-dev.yaml

# Test import paths
python -c "from services.api_gateway.src.app.main import app; print('✅ Imports working')"

# Validate workflows
act --list
```

## Risk Mitigation

### High-Risk Changes
1. **Import path updates**: Create automated migration script with rollback
2. **Dockerfile changes**: Maintain parallel build during transition
3. **Workflow consolidation**: Keep original workflows as backup during testing

### Rollback Procedures
```bash
# Complete rollback script
#!/bin/bash
set -e

echo "Rolling back directory structure changes..."
git mv services/api-gateway/src/app/ app/
git mv apps/web-ui/src/ src/
git mv db/migrations/ migrations/
git mv db/alembic.ini alembic.ini

echo "Restoring original workflows..."
git checkout HEAD~1 -- .github/workflows/

echo "Rollback complete. Run tests to validate."
```

## Implementation Timeline

### Week 1: Structure + Docker
- **Day 1-2**: Directory reorganization and import path updates
- **Day 3-4**: Docker standardization and .dockerignore
- **Day 5**: Validation and testing

### Week 2: CI/CD Consolidation  
- **Day 1-2**: Create reusable actions
- **Day 3-4**: Consolidate workflows
- **Day 5**: Security scanning standardization

### Week 3: Helm Migration
- **Day 1-2**: Create Helm charts
- **Day 3-4**: Environment-specific values
- **Day 5**: K8s deployment validation

### Week 4: Documentation + Cleanup
- **Day 1-2**: Update all documentation
- **Day 3-4**: Final validation and testing
- **Day 5**: Archive old assets to .attic/

---

**Approval Required**: This plan requires stakeholder approval before execution. All changes preserve git history and include comprehensive rollback procedures.
