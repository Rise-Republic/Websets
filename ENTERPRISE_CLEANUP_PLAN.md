# Enterprise Multitenant SaaS Repo Cleanup & Reorganization Plan

**Repository**: WebSets Multi-tenant B2B SaaS Platform  
**Architecture**: Multitenant SaaS; FastAPI + React + Celery Workers  
**Runtime**: Docker, Kubernetes, Docker Compose for local dev  
**Infra-as-Code**: Terraform, GitHub Actions, GHCR  
**Datastores**: PostgreSQL + Redis + Qdrant + Weaviate with Alembic migrations  
**Security**: SBOM generation, Trivy scanning, Gitleaks, least-privilege containers  

## Context & Current State

**Repository Type**: Monorepo  
**Tenancy Model**: Shared schema with tenant_id isolation + RLS policies  
**Data Partitioning**: Context-aware tenant scoping with SQLAlchemy hooks  
**Environments**: development, staging, production  
**Container Registry**: GitHub Container Registry (GHCR)  
**Languages**: Python 3.11+, TypeScript/React, Shell scripts  

## Objectives (Priority Order)

1. **Eliminate redundancy**: Remove duplicate workflows, old artifacts, stale configs
2. **Remove dead code**: Clean unused manifests and unreferenced assets  
3. **Normalize structure**: Standardize service, infra, and environment organization
4. **Standardize containers**: Multi-stage Dockerfiles, distroless bases, non-root users
5. **Consolidate CI**: Reusable workflows, centralized security scanning
6. **Enforce conventions**: Consistent naming, tagging, versioning across all assets
7. **Improve discoverability**: Clear documentation, runbooks, service quickstarts

## Target Enterprise Structure

```
/apps/                       # Customer-facing applications
  /web-ui/                   # React frontend application
    /src/
    /public/
    Dockerfile
    package.json
    .dockerignore
/services/                   # Backend microservices and workers
  /api-gateway/              # FastAPI main application
    /src/
    /app/                    # Current app/ directory content
    /tests/
    Dockerfile
    requirements.txt
    .dockerignore
  /worker-celery/            # Celery background workers
    /src/
    /tasks/
    Dockerfile
    requirements.txt
/packages/                   # Shared libraries and utilities
  /python-common/            # Shared Python utilities
  /typescript-common/        # Shared TypeScript components
/db/                        # Database assets
  /migrations/               # Alembic migrations (moved from migrations/)
  /seeds/                    # Test data and initial seeds
/deploy/                    # Deployment configurations
  /helm/                     # Helm charts for K8s deployment
    /websets/               # Main application chart
      /templates/
      /values/
        values-dev.yaml
        values-staging.yaml
        values-prod.yaml
  /docker-compose/           # Local development compose files
    docker-compose.yml
    docker-compose.override.yml
/infra/                     # Infrastructure as Code
  /terraform/               # Terraform configurations
    /environments/
      /dev/
      /staging/
      /prod/
    /modules/               # Reusable Terraform modules
/scripts/                   # Developer and CI utilities
  /dev/                     # Development helper scripts
  /ci/                      # CI-specific scripts
  /ops/                     # Operations scripts
/tools/                     # Code quality and development tools
  /linting/                 # Linting configurations
  /security/                # Security scanning configs
/docs/                      # Documentation
  /architecture/            # System architecture docs
  /runbooks/                # Operational runbooks
  /api/                     # API documentation
/.github/                   # GitHub configurations
  /workflows/               # Standardized CI/CD workflows
  /templates/               # Issue/PR templates
.attic/                     # Quarantine for deprecated assets (30-day retention)
```

## Naming & Tagging Conventions

**Directories**: kebab-case (`api-gateway`, `web-ui`)  
**Docker Images**: `ghcr.io/rise-republic/websets-{service}:{tag}`  
**Branches**: `feat/`, `fix/`, `chore/`, `ops/`, `security/`  
**Image Tags**: 
- Releases: `v1.2.3` (semver)
- CI builds: `sha-{git-sha}`
- **Forbidden**: `latest` in production
**Helm Charts**: Chart name equals service name  
**Values Files**: `values-{env}.yaml` pattern  

## Phase 1: Inventory & Analysis

### Repository Manifest Analysis

Current structure analysis shows:
- **27 GitHub Actions workflows** (potential consolidation opportunities)
- **Mixed directory patterns** (app/, src/, inconsistent naming)
- **Multiple Docker configurations** (needs standardization)
- **Scattered configuration files** (needs centralization)
- **Documentation spread across multiple locations**

### Dependency Graph Findings

**Service Dependencies**:
- FastAPI backend → PostgreSQL, Redis, Qdrant, Weaviate
- React frontend → FastAPI API endpoints  
- Celery workers → Redis broker, PostgreSQL, vector databases
- Monitoring → Prometheus, Grafana, AlertManager

**Build Dependencies**:
- Python services use requirements.txt
- Frontend uses npm/package.json
- Docker builds reference multiple contexts
- Terraform modules have cross-dependencies

### Docker/K8s Audit Results

**Current Issues**:
- ❌ Single-stage Dockerfiles (security risk)
- ❌ Root user containers (privilege escalation risk)  
- ❌ Missing .dockerignore files (build context bloat)
- ❌ No HEALTHCHECK directives (poor observability)
- ❌ Inconsistent base images (maintenance burden)
- ❌ K8s manifests scattered across directories

**Security Gaps**:
- Missing container vulnerability scanning in some workflows
- Inconsistent SBOM generation
- No container signing verification

### CI/CD Audit Results

**Duplicate Patterns**:
- Security scanning duplicated across 5+ workflows
- Lint/format jobs repeated per service
- Docker build patterns inconsistent
- Missing matrix builds for multi-service repo

**Missing Security Gates**:
- Some workflows lack Trivy container scanning
- Inconsistent secret scanning coverage
- SBOM generation not standardized
- Container signing not implemented everywhere

## Phase 2: Cleanup Plan

### Directory Reorganization

| Current Location | Target Location | Rationale |
|-----------------|----------------|-----------|
| `app/` | `services/api-gateway/src/app/` | Service-centric organization |
| `src/` | `apps/web-ui/src/` | Separate frontend application |
| `migrations/` | `db/migrations/` | Centralized database assets |
| `k8s/` | `deploy/helm/websets/templates/` | Helm-based deployment |
| `infra/terraform/` | `infra/terraform/environments/` | Environment-specific configs |
| `scripts/` | `scripts/` (reorganize) | Categorize by purpose |
| `tests/` | `services/*/tests/` | Co-locate with services |
| `monitoring/` | `deploy/helm/websets/templates/monitoring/` | K8s native monitoring |

### File Standardization Plan

**Dockerfiles**:
```dockerfile
# Multi-stage build pattern
FROM python:3.11-slim as builder
# Build dependencies and virtual env

FROM gcr.io/distroless/python3-debian12 as runtime
# Minimal runtime with non-root user
USER 65534
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**CI Consolidation**:
- Create reusable workflow templates in `.github/workflows/templates/`
- Implement matrix builds for multi-service scenarios
- Centralize security scanning in dedicated workflow
- Add SBOM generation to all container builds

### Environment Configuration

**Centralized Config Pattern**:
```yaml
# deploy/helm/websets/values/values-prod.yaml
global:
  environment: production
  registry: ghcr.io/rise-republic
  
services:
  api-gateway:
    image:
      tag: v1.2.3
    replicas: 3
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
```

## Phase 3: Implementation PRs

### PR 1: `refactor(structure): reorganize services and apps`
- Move `app/` → `services/api-gateway/src/app/`
- Move `src/` → `apps/web-ui/src/`
- Update all import paths and references
- **Risk**: Medium - requires import path updates
- **Rollback**: Git revert + path restoration script

### PR 2: `chore(docker): standardize containers and security`
- Implement multi-stage Dockerfiles
- Add .dockerignore files
- Switch to distroless base images
- Add non-root user and HEALTHCHECK
- **Risk**: Low - backward compatible changes
- **Rollback**: Revert Dockerfile changes

### PR 3: `build(ci): centralize workflows and add security gates`
- Create reusable workflow templates
- Add comprehensive SBOM generation
- Implement container signing with Cosign
- Standardize security scanning across all services
- **Risk**: Low - additive security improvements
- **Rollback**: Disable new workflows, revert to originals

### PR 4: `feat(deploy): migrate to Helm-based deployment`
- Convert K8s manifests to Helm charts
- Create environment-specific values files
- Add Helm validation to CI
- **Risk**: Medium - deployment method change
- **Rollback**: Keep old K8s manifests as backup

### PR 5: `docs: update documentation and runbooks`
- Create service-specific READMEs
- Update operational runbooks
- Add architecture decision records
- **Risk**: None - documentation only
- **Rollback**: Not applicable

## Phase 4: Documentation & Handoff

### Updated Documentation Structure

```
docs/
├── README.md                    # Repository overview and quickstart
├── architecture/
│   ├── system-overview.md       # High-level architecture
│   ├── data-flow.md            # Request/data flow diagrams  
│   └── security-model.md       # Security architecture
├── runbooks/
│   ├── deployment.md           # Deployment procedures
│   ├── monitoring.md           # Monitoring and alerting
│   ├── incident-response.md    # Incident handling
│   └── rollback.md            # Emergency rollback procedures
├── development/
│   ├── getting-started.md      # Local development setup
│   ├── testing.md             # Testing guidelines
│   └── contributing.md        # Contribution guidelines
└── api/
    └── openapi.yaml           # API specification
```

## Validation Requirements

### Pre-merge Checks
- ✅ All CI workflows pass (lint, test, build, scan)
- ✅ Docker builds succeed for all services
- ✅ Helm charts validate and dry-run install
- ✅ Terraform plans execute cleanly
- ✅ SBOM generation produces valid artifacts
- ✅ Container security scans pass
- ✅ No secrets detected in code

### Post-merge Validation
- ✅ Local development environment works (`docker-compose up`)
- ✅ Staging deployment succeeds
- ✅ All monitoring dashboards functional
- ✅ API compatibility maintained
- ✅ Performance benchmarks meet SLA

## Risk Mitigation

### High-Risk Changes
1. **Service reorganization**: Gradual migration with feature flags
2. **Container standardization**: Parallel builds during transition
3. **Helm migration**: Blue-green deployment with rollback plan

### Safety Measures
- All changes preserve git history (`git mv` commands)
- Contested files moved to `.attic/` with 30-day retention
- Comprehensive rollback procedures documented
- Feature flags for gradual service migration

## Success Metrics

### Quantitative Goals
- **Build time reduction**: 30% faster CI/CD pipelines
- **Security coverage**: 100% SBOM + vulnerability scanning
- **Documentation coverage**: 100% services with quickstart guides
- **Deployment reliability**: <2 minute rollback capability

### Qualitative Improvements
- New developer onboarding time reduced to <30 minutes
- Consistent patterns across all services and environments
- Enterprise-grade security posture with audit trails
- Simplified operational procedures with automated runbooks

## Implementation Timeline

**Week 1**: Phase 1 completion + Phase 2 planning approval  
**Week 2**: PRs 1-2 (structure + containers)  
**Week 3**: PRs 3-4 (CI + deployment)  
**Week 4**: PR 5 + documentation + validation  

Total estimated effort: **4 weeks** with 2 engineers

---

**Next Steps**: Execute Phase 1 inventory analysis and generate detailed reports for stakeholder review.
