# WebSets - Enterprise Multi-tenant B2B SaaS Platform

**WebSets** is a sophisticated multi-tenant B2B SaaS platform for autonomous web data discovery and extraction, built with enterprise-grade security, scalability, and operational excellence.

## 🏗️ Architecture Overview

### Technology Stack
- **Frontend**: React 18.3.1 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python 3.11+ + SQLAlchemy + PostgreSQL
- **Authentication**: WorkOS AuthKit + JWT with MFA support
- **Infrastructure**: Docker + Kubernetes + Terraform
- **Monitoring**: Prometheus + Grafana + OpenTelemetry
- **CI/CD**: GitHub Actions with comprehensive security scanning

### Multi-tenancy Model
- **Pattern**: Shared schema with tenant_id isolation
- **Security**: Row-level security (RLS) with context-aware tenant scoping
- **Data Isolation**: SQLAlchemy hooks ensure bulletproof tenant separation
- **Compliance**: SOC2, HIPAA, GDPR, and FedRAMP alignment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+ and pip
- kubectl (for K8s deployment)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/rise-republic/websets.git
cd websets

# Start local development environment
docker-compose -f deploy/docker-compose/docker-compose.yml up -d

# Install frontend dependencies
cd apps/web-ui
npm install
npm run dev

# Install backend dependencies (in another terminal)
cd services/api-gateway
pip install -r requirements.txt
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
cd ../../db
alembic upgrade head
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Repository Structure

```
├── apps/                    # Customer-facing applications
│   └── web-ui/             # React frontend application
├── services/               # Backend microservices
│   ├── api-gateway/        # Main FastAPI service
│   └── worker-celery/      # Background workers
├── packages/               # Shared libraries and utilities
├── db/                     # Database migrations and seeds
├── deploy/                 # Deployment configurations
│   ├── helm/              # Kubernetes Helm charts
│   └── docker-compose/    # Local development
├── infra/                  # Infrastructure as Code (Terraform)
├── scripts/                # Development and operations scripts
├── tools/                  # Code quality and security tools
├── docs/                   # Comprehensive documentation
└── .github/               # CI/CD workflows and reusable actions
```

## 🔒 Security & Compliance

### Security Features
- **Zero-trust architecture** with comprehensive threat protection
- **Multi-layer scanning**: SAST, DAST, container, dependency, and secret scanning
- **SBOM generation** with Cosign artifact signing
- **Field-level encryption** for sensitive data
- **Comprehensive audit trails** with tenant isolation

### Compliance Standards
- **SOC2 Type II** controls implementation
- **GDPR** compliance with data portability and right to erasure
- **HIPAA** alignment for healthcare data processing
- **FedRAMP** controls for government sector deployment

## 🛠️ Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feat/` - Feature development branches
- `fix/` - Bug fix branches
- `security/` - Security-related changes

### CI/CD Pipeline
1. **Security Scan** - Comprehensive security analysis
2. **Build & Test** - Multi-service build with testing
3. **Deploy Dev** - Automatic deployment to development
4. **Deploy Staging** - Deployment to staging environment
5. **Deploy Production** - Manual approval for production

### Code Quality Standards
- **Test Coverage**: 80%+ across all services
- **TypeScript**: Strict mode with zero `any` types
- **Python**: Ruff linting + Black formatting + MyPy type checking
- **Security**: Zero high/critical vulnerabilities

## 🚀 Deployment

### Development Environment
```bash
# Deploy to development
kubectl apply -f deploy/helm/websets/templates/ --namespace=websets-dev
```

### Staging Environment
```bash
# Deploy using Helm
helm upgrade --install websets-staging deploy/helm/websets/ \
  --namespace=websets-staging \
  --values=deploy/helm/websets/values/values-staging.yaml
```

### Production Environment
```bash
# Production deployment (requires approval)
gh workflow run production-deploy.yml \
  --field version=v1.2.3 \
  --field environment=production \
  --field deployment_strategy=blue-green
```

## 📊 Monitoring & Observability

### Monitoring Stack
- **Metrics**: Prometheus with tenant-aware collection
- **Dashboards**: Grafana with tenant-segmented views
- **Alerting**: AlertManager with tenant-specific routing
- **Tracing**: OpenTelemetry distributed tracing
- **Logs**: Structured logging with tenant context

### Key Metrics
- **Performance**: P95 latency <500ms, throughput >1000 RPS
- **Availability**: 99.9% uptime SLA
- **Security**: Zero critical vulnerabilities
- **Compliance**: 100% audit trail coverage

## 🔧 Operations

### Runbooks
- [Deployment Procedures](docs/runbooks/deployment.md)
- [Monitoring & Alerting](docs/runbooks/monitoring.md)
- [Incident Response](docs/runbooks/incident-response.md)
- [Emergency Rollback](docs/runbooks/rollback.md)

### Emergency Procedures
```bash
# Emergency rollback
gh workflow run rollback.yml \
  --field target_version=v1.2.2 \
  --field environment=production \
  --field rollback_reason="Critical bug"
```

## 🧪 Testing

### Test Suites
- **Unit Tests**: Jest (frontend) + pytest (backend)
- **Integration Tests**: API integration with test database
- **Contract Tests**: Pact consumer/provider testing
- **Performance Tests**: k6 load testing with SLA validation
- **Accessibility Tests**: axe-core WCAG 2.1 AA compliance
- **Security Tests**: Automated vulnerability scanning

### Running Tests
```bash
# Frontend tests
cd apps/web-ui
npm test

# Backend tests
cd services/api-gateway
python -m pytest tests/ --cov=src --cov-report=html

# Integration tests
python -m pytest tests/integration/ -v

# Performance tests
k6 run tests/performance/load-test.js
```

## 📚 Documentation

### Developer Resources
- [Architecture Overview](docs/architecture/system-overview.md)
- [API Reference](docs/api/openapi.yaml)
- [Development Guide](docs/development/getting-started.md)
- [Contributing Guidelines](docs/development/contributing.md)

### Operational Resources
- [Deployment Runbook](docs/runbooks/deployment.md)
- [Monitoring Guide](docs/runbooks/monitoring.md)
- [Security Procedures](docs/runbooks/security.md)
- [Incident Response](docs/runbooks/incident-response.md)

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes and add tests
4. Ensure all CI checks pass
5. Submit a pull request

### Code Standards
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure security scans pass
- Maintain test coverage above 80%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Security**: Report security issues to security@websets.com
- **Support**: Contact support@websets.com for operational issues

### Status & Health
- **Production Status**: https://status.websets.com
- **Health Endpoint**: https://api.websets.com/health
- **Metrics Dashboard**: https://metrics.websets.com

---

**Built with ❤️ by the WebSets Platform Team**

*Enterprise-grade • Secure by design • Production ready*
