# WebSets Repository Migration Runbook

## Overview
This runbook provides step-by-step procedures for migrating from the legacy WebSets structure to the new enterprise architecture.

## Pre-Migration Checklist

### Environment Preparation
- [ ] Backup current repository state
- [ ] Verify Docker and Docker Compose installed
- [ ] Ensure Node.js 20+ available
- [ ] Confirm Python 3.13+ environment
- [ ] Test database connectivity

### Validation Scripts
```bash
# Run pre-migration validation
./scripts/validate-migration.sh

# Check current structure
find . -maxdepth 2 -type d | sort
```

## Migration Procedures

### Phase 1: Structure Creation
```bash
# Create enterprise directory structure
mkdir -p apps/{web-ui,api-gateway}
mkdir -p services/{auth-service,data-mining,vector-search}
mkdir -p packages/{shared-types,common-utils}
mkdir -p db/{migrations,seeds,schemas}
mkdir -p deploy/{helm,kustomize,compose}
```

### Phase 2: Application Migration

#### Frontend Migration
```bash
# Copy frontend files to new location
cp -r src/ apps/web-ui/src/
cp package.json apps/web-ui/
cp package-lock.json apps/web-ui/
cp index.html apps/web-ui/
cp vite.config.ts apps/web-ui/
cp tailwind.config.js apps/web-ui/
cp postcss.config.js apps/web-ui/
cp tsconfig*.json apps/web-ui/

# Update configuration
cd apps/web-ui
cp .env.example .env
# Edit .env with correct values
```

#### Backend Migration
```bash
# Copy backend files to new location
cp -r app/ apps/api-gateway/app/
cp requirements.txt apps/api-gateway/
cp requirements-dev.txt apps/api-gateway/
cp alembic.ini apps/api-gateway/

# Update import paths if needed
# (Most imports should work due to relative paths)
```

#### Database Migration
```bash
# Move database files
cp -r migrations/ db/migrations/
```

### Phase 3: Docker Configuration

#### Build New Images
```bash
# Build frontend
docker build -t websets/web-ui:latest apps/web-ui/

# Build backend
docker build -t websets/api-gateway:latest apps/api-gateway/
```

#### Deploy with New Compose
```bash
# Start new stack
docker-compose -f deploy/compose/docker-compose.new.yml up -d

# Verify services
docker-compose -f deploy/compose/docker-compose.new.yml ps
```

## Validation Procedures

### Service Health Checks
```bash
# Frontend health
curl -f http://localhost:3000 || echo "Frontend not ready"

# Backend health
curl -f http://localhost:8000/health || echo "Backend not ready"

# Database connectivity
docker exec compose-postgres-1 pg_isready -U postgres
```

### Functional Testing
```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/v1/status

# Test frontend routing
curl -s http://localhost:3000 | grep -o '<title>.*</title>'

# Test database migrations
docker exec compose-api-gateway-1 alembic current
```

## Rollback Procedures

### Emergency Rollback
```bash
# Stop new services
docker-compose -f deploy/compose/docker-compose.new.yml down

# Restore original services
docker-compose up -d

# Verify original functionality
curl -f http://localhost:5173 # Original frontend
curl -f http://localhost:8000/health # Original backend
```

### Selective Rollback
```bash
# Rollback frontend only
docker-compose -f deploy/compose/docker-compose.new.yml stop web-ui
# Start original frontend development server
cd /original/location && npm run dev

# Rollback backend only
docker-compose -f deploy/compose/docker-compose.new.yml stop api-gateway
# Start original backend
uvicorn app.main:app --reload
```

## Troubleshooting Guide

### Common Issues

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
netstat -tulpn | grep :9000

# Solution: Update docker-compose.new.yml ports
# postgres: 5433:5432
# redis: 6380:6379
# minio: 9002:9000, 9003:9001
```

#### CORS Errors
```bash
# Check API configuration
grep -r "allowed_origins" apps/api-gateway/app/config/

# Verify frontend URL in CORS settings
# Should include: http://localhost:3000
```

#### Environment Variables
```bash
# Check required variables
docker exec compose-api-gateway-1 env | grep -E "(DATABASE_URL|REDIS_URL|OPENAI_API_KEY)"

# Add missing variables to docker-compose.new.yml
```

#### Build Failures
```bash
# Frontend build issues
cd apps/web-ui
npm install
npm run build

# Backend build issues
cd apps/api-gateway
pip install -r requirements.txt
```

### Log Analysis
```bash
# Frontend logs
docker logs compose-web-ui-1 --tail 50

# Backend logs
docker logs compose-api-gateway-1 --tail 50

# Database logs
docker logs compose-postgres-1 --tail 20
```

## Post-Migration Tasks

### Cleanup
```bash
# Remove redundant files (after validation)
rm Dockerfile.backend

# Update .gitignore if needed
echo "apps/*/.env" >> .gitignore
```

### Documentation Updates
- [ ] Update main README.md
- [ ] Create service-specific READMEs
- [ ] Update deployment documentation
- [ ] Update development setup guides

### CI/CD Updates
- [ ] Update GitHub Actions workflows
- [ ] Update build paths
- [ ] Update deployment scripts
- [ ] Test CI/CD pipeline

## Success Criteria

### Technical Validation
- [ ] All services start successfully
- [ ] Health checks pass
- [ ] API endpoints respond correctly
- [ ] Frontend loads and functions
- [ ] Database migrations complete
- [ ] Authentication works

### Performance Validation
- [ ] Response times within acceptable range
- [ ] Memory usage stable
- [ ] No resource leaks
- [ ] Build times reasonable

### Security Validation
- [ ] CORS configured correctly
- [ ] Authentication working
- [ ] No exposed secrets
- [ ] Security headers present

## Emergency Contacts

### Development Team
- **Lead Developer**: [Contact Info]
- **DevOps Engineer**: [Contact Info]
- **Database Administrator**: [Contact Info]

### Escalation Procedures
1. Check service logs
2. Attempt automated rollback
3. Contact development team
4. Escalate to management if needed

## Appendix

### Useful Commands
```bash
# Quick status check
docker-compose -f deploy/compose/docker-compose.new.yml ps

# View all logs
docker-compose -f deploy/compose/docker-compose.new.yml logs

# Restart specific service
docker-compose -f deploy/compose/docker-compose.new.yml restart api-gateway

# Execute commands in container
docker exec -it compose-api-gateway-1 bash
```

### Configuration Files
- `deploy/compose/docker-compose.new.yml` - New Docker Compose configuration
- `apps/web-ui/.env` - Frontend environment variables
- `apps/api-gateway/app/config/` - Backend configuration
- `scripts/migrate-structure.sh` - Migration automation script
