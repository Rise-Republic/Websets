# WebSets Enterprise Repository Cleanup Plan

## Executive Summary
This plan outlines the systematic refactoring of the WebSets monorepo to align with enterprise best practices for a multitenant SaaS platform. The cleanup will be executed in atomic phases to minimize risk while maximizing maintainability and scalability.

## Current State Analysis
- **17,949 source files** across mixed directory structure
- **Dual application structure**: `/app` (backend) + `/src` (frontend)
- **29 GitHub Actions workflows** with redundancy
- **2 Docker strategies** creating deployment confusion
- **Scattered configuration** across multiple locations

## Target Enterprise Structure

```
websets/
├── apps/                    # Customer-facing applications
│   ├── web-ui/             # React frontend application
│   │   ├── src/
│   │   ├── package.json
│   │   └── Dockerfile
│   └── api-gateway/        # Main API gateway
│       ├── app/
│       ├── requirements.txt
│       └── Dockerfile
├── services/               # Microservices and workers
│   ├── auth-service/       # Authentication microservice
│   ├── data-mining/        # Mining jobs and workers
│   ├── vector-search/      # Search and embeddings
│   └── notification/       # Notification service
├── packages/               # Shared libraries
│   ├── shared-types/       # TypeScript definitions
│   ├── common-utils/       # Shared utilities
│   └── api-client/         # Generated API clients
├── db/                     # Database management
│   ├── migrations/         # Alembic migrations
│   ├── seeds/             # Test data
│   └── schemas/           # Database schemas
├── deploy/                 # Deployment configurations
│   ├── helm/              # Helm charts
│   ├── kustomize/         # Kustomize overlays
│   └── compose/           # Docker Compose files
├── infra/                  # Infrastructure as code
│   ├── terraform/         # Terraform modules
│   └── monitoring/        # Observability configs
├── scripts/                # Utility scripts
├── tools/                  # Development tools
├── docs/                   # Documentation
└── .github/               # CI/CD workflows
    └── workflows/
```

## Phase 1: Foundation & Analysis ✅
**Status**: COMPLETED
- [x] Generate comprehensive inventory report
- [x] Audit Docker configurations
- [x] Analyze CI/CD workflows
- [x] Assess secrets and configuration management
- [x] Document current state and issues

## Phase 2: Structure Preparation
**Timeline**: 2-3 days
**Risk Level**: Low

### 2.1 Create Target Directory Structure
```bash
mkdir -p {apps/{web-ui,api-gateway},services/{auth-service,data-mining,vector-search},packages/{shared-types,common-utils},db/{migrations,seeds,schemas},deploy/{helm,kustomize,compose},tools,docs}
```

### 2.2 Prepare Migration Scripts
- Create automated migration scripts for file moves
- Implement validation scripts for structure integrity
- Prepare rollback procedures

### 2.3 Update Build Configurations
- Create service-specific Dockerfiles
- Update package.json and requirements.txt paths
- Prepare new CI/CD workflow templates

## Phase 3: Core Application Migration
**Timeline**: 3-4 days
**Risk Level**: Medium

### 3.1 Frontend Application Migration
**Target**: `apps/web-ui/`
```bash
# Move frontend application
mv src/ apps/web-ui/src/
mv package.json apps/web-ui/
mv package-lock.json apps/web-ui/
mv index.html apps/web-ui/
mv vite.config.ts apps/web-ui/
mv tailwind.config.js apps/web-ui/
mv postcss.config.js apps/web-ui/
mv tsconfig*.json apps/web-ui/
```

### 3.2 Backend API Migration
**Target**: `apps/api-gateway/`
```bash
# Move backend application
mv app/ apps/api-gateway/app/
mv requirements.txt apps/api-gateway/
mv requirements-dev.txt apps/api-gateway/
```

### 3.3 Database Migration
**Target**: `db/`
```bash
# Move database files
mv migrations/ db/migrations/
mv alembic.ini db/
```

### 3.4 Update Import Paths
- Update Python imports to reflect new structure
- Update TypeScript imports and paths
- Update configuration file references

## Phase 4: Service Extraction
**Timeline**: 4-5 days
**Risk Level**: Medium-High

### 4.1 Authentication Service
**Target**: `services/auth-service/`
- Extract auth-related modules from main app
- Create dedicated service structure
- Update API contracts and dependencies

### 4.2 Data Mining Service
**Target**: `services/data-mining/`
- Extract mining and processing logic
- Separate worker processes
- Update job queue configurations

### 4.3 Vector Search Service
**Target**: `services/vector-search/`
- Extract search and embedding logic
- Separate vector database interactions
- Update search API endpoints

## Phase 5: Infrastructure Consolidation
**Timeline**: 2-3 days
**Risk Level**: Low-Medium

### 5.1 Docker Standardization
- Remove redundant `Dockerfile.backend`
- Create service-specific Dockerfiles
- Implement multi-stage build optimization
- Update docker-compose configurations

### 5.2 Kubernetes Migration
**Target**: `deploy/helm/`
```bash
# Move and organize K8s configs
mv k8s/ deploy/helm/templates/
```

### 5.3 Infrastructure Code
**Target**: `infra/`
- Consolidate Terraform modules
- Move monitoring configurations
- Update infrastructure documentation

## Phase 6: CI/CD Optimization
**Timeline**: 2-3 days
**Risk Level**: Medium

### 6.1 Workflow Consolidation
**Remove Redundant Workflows**:
- `security.yml`, `security-enhanced.yml` → Keep `security-comprehensive.yml`
- `ci.yml` → Merge into `test.yml`
- `docker-deploy.yml`, `fargate-deploy.yml` → Consolidate into `deploy.yml`

**Target Structure**:
```
.github/workflows/
├── ci.yml                  # Main CI pipeline
├── security.yml            # Consolidated security
├── test.yml               # Comprehensive testing
├── deploy-staging.yml     # Staging deployment
├── deploy-production.yml  # Production deployment
├── release.yml            # Release management
└── maintenance.yml        # Scheduled tasks
```

### 6.2 Create Reusable Templates
- Extract common workflow patterns
- Implement workflow templates
- Update workflow triggers and dependencies

## Phase 7: Configuration Standardization
**Timeline**: 1-2 days
**Risk Level**: Low

### 7.1 Environment Configuration
- Create configuration schema
- Implement validation logic
- Standardize environment files

### 7.2 Documentation Updates
- Update all README files
- Create service-specific documentation
- Update deployment guides

## Risk Mitigation Strategies

### 1. Atomic Changes
- Each phase implemented as separate PRs
- Comprehensive testing before merge
- Rollback procedures documented

### 2. Validation Scripts
- Automated structure validation
- Import path verification
- Build process validation

### 3. Backward Compatibility
- Maintain API surface compatibility
- Preserve git history
- Keep existing deployment working during transition

### 4. Testing Strategy
- Run full test suite after each phase
- Integration testing for service boundaries
- Performance testing for new structure

## Success Metrics

### Technical Metrics
- [ ] All tests passing in new structure
- [ ] Build times maintained or improved
- [ ] No broken imports or dependencies
- [ ] All services deployable independently

### Operational Metrics
- [ ] Reduced CI/CD complexity (target: <15 workflows)
- [ ] Improved build caching efficiency
- [ ] Clear service boundaries established
- [ ] Documentation completeness >90%

## Timeline Summary
- **Phase 1**: ✅ Completed (Analysis)
- **Phase 2**: 2-3 days (Structure Preparation)
- **Phase 3**: 3-4 days (Core Migration)
- **Phase 4**: 4-5 days (Service Extraction)
- **Phase 5**: 2-3 days (Infrastructure)
- **Phase 6**: 2-3 days (CI/CD)
- **Phase 7**: 1-2 days (Configuration)

**Total Estimated Time**: 14-20 days
**Risk Level**: Medium (with proper validation and rollback procedures)

## Next Steps
1. Review and approve cleanup plan
2. Begin Phase 2: Structure Preparation
3. Create migration scripts and validation tools
4. Execute phases with comprehensive testing
