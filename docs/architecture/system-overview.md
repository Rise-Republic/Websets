# WebSets System Architecture Overview

## Executive Summary

WebSets is an enterprise-grade multi-tenant B2B SaaS platform designed for autonomous web data discovery and extraction. The system employs a microservices architecture with strict tenant isolation, comprehensive security controls, and enterprise-grade operational capabilities.

## Architecture Principles

### Design Philosophy
- **Security by Design**: Zero-trust architecture with defense in depth
- **Multi-tenancy First**: Tenant isolation at every layer of the stack
- **Cloud Native**: Kubernetes-native with 12-factor app principles
- **Observability**: Comprehensive monitoring, logging, and tracing
- **Compliance Ready**: SOC2, HIPAA, GDPR, and FedRAMP alignment

### Quality Attributes
- **Availability**: 99.9% uptime SLA with automated failover
- **Performance**: <500ms P95 latency, >1000 RPS throughput
- **Scalability**: Horizontal scaling with auto-scaling policies
- **Security**: Zero critical vulnerabilities, comprehensive audit trails
- **Maintainability**: Modular design with clear separation of concerns

## System Context

```mermaid
graph TB
    subgraph "External Systems"
        U[End Users] 
        A[Admin Users]
        W[WorkOS AuthKit]
        S[External APIs]
        M[Monitoring Services]
    end
    
    subgraph "WebSets Platform"
        WS[WebSets System]
    end
    
    U --> WS
    A --> WS
    W --> WS
    WS --> S
    WS --> M
```

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Application]
        MOB[Mobile App]
        API_CLIENT[API Clients]
    end
    
    subgraph "Edge Layer"
        CDN[CloudFlare CDN]
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph "Application Layer"
        GATEWAY[API Gateway]
        AUTH[Auth Service]
        CORE[Core Services]
        WORKER[Background Workers]
    end
    
    subgraph "Data Layer"
        PG[PostgreSQL]
        REDIS[Redis Cache]
        QDRANT[Qdrant Vector DB]
        S3[Object Storage]
    end
    
    subgraph "Infrastructure Layer"
        K8S[Kubernetes Cluster]
        MONITOR[Monitoring Stack]
        SECURITY[Security Services]
    end
    
    WEB --> CDN
    MOB --> CDN
    API_CLIENT --> CDN
    
    CDN --> WAF
    WAF --> LB
    LB --> GATEWAY
    
    GATEWAY --> AUTH
    GATEWAY --> CORE
    CORE --> WORKER
    
    AUTH --> PG
    CORE --> PG
    CORE --> REDIS
    CORE --> QDRANT
    WORKER --> S3
    
    K8S --> MONITOR
    K8S --> SECURITY
```

## Service Architecture

### Microservices Overview

| Service | Purpose | Technology | Scaling |
|---------|---------|------------|---------|
| **API Gateway** | Request routing, rate limiting, auth | FastAPI + Python | Horizontal |
| **Auth Service** | Authentication, authorization, RBAC | FastAPI + WorkOS | Horizontal |
| **Core Services** | Business logic, data processing | FastAPI + SQLAlchemy | Horizontal |
| **Worker Service** | Background jobs, data extraction | Celery + Python | Horizontal |
| **Web UI** | User interface, dashboard | React + TypeScript | CDN |

### Service Communication

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as Auth Service
    participant S as Core Service
    participant W as Worker
    participant D as Database
    
    C->>G: HTTP Request
    G->>A: Validate Token
    A->>G: User Context
    G->>S: Authorized Request
    S->>D: Query Data
    D->>S: Result Set
    S->>W: Queue Background Job
    S->>G: Response
    G->>C: HTTP Response
    
    Note over W: Async Processing
    W->>D: Update Status
```

## Multi-Tenancy Architecture

### Tenant Isolation Model

```mermaid
graph TB
    subgraph "Shared Infrastructure"
        subgraph "Application Layer"
            APP[Multi-tenant Application]
        end
        
        subgraph "Data Layer - Shared Schema"
            DB[(PostgreSQL Database)]
            
            subgraph "Tenant A Data"
                TA_U[Users: tenant_id=A]
                TA_D[Data: tenant_id=A]
            end
            
            subgraph "Tenant B Data"
                TB_U[Users: tenant_id=B]
                TB_D[Data: tenant_id=B]
            end
        end
    end
    
    APP --> DB
    APP -.-> TA_U
    APP -.-> TA_D
    APP -.-> TB_U
    APP -.-> TB_D
```

### Tenant Context Management

```python
# Tenant context enforcement at ORM level
@event.listens_for(Session, "do_orm_execute", propagate=True)
def _add_tenant_criteria(execute_state) -> None:
    tenant_id = _current_tenant.get()
    if tenant_id and execute_state.is_select:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                cls, 
                lambda cls: cls.tenant_id == tenant_id, 
                include_aliases=True
            )
        )
```

### Security Boundaries

1. **Network Level**: VPC isolation, security groups
2. **Application Level**: Tenant context validation
3. **Data Level**: Row-level security with tenant_id
4. **API Level**: JWT claims validation
5. **UI Level**: Tenant-scoped data presentation

## Data Architecture

### Database Design

```mermaid
erDiagram
    TENANT ||--o{ USER : contains
    TENANT ||--o{ DATASET : owns
    USER ||--o{ AUDIT_LOG : generates
    USER }o--o{ ROLE : has
    ROLE ||--o{ PERMISSION : grants
    DATASET ||--o{ EXTRACTION_JOB : triggers
    EXTRACTION_JOB ||--o{ RESULT : produces
    
    TENANT {
        uuid id PK
        string name
        string subdomain
        jsonb settings
        timestamp created_at
        timestamp updated_at
    }
    
    USER {
        uuid id PK
        uuid tenant_id FK
        string email
        string encrypted_password
        boolean mfa_enabled
        timestamp last_login
        timestamp created_at
    }
    
    DATASET {
        uuid id PK
        uuid tenant_id FK
        uuid owner_id FK
        string name
        jsonb schema
        jsonb metadata
        timestamp created_at
    }
```

### Data Flow Architecture

```mermaid
graph LR
    subgraph "Ingestion"
        API[REST API]
        WEBHOOK[Webhooks]
        UPLOAD[File Upload]
    end
    
    subgraph "Processing"
        QUEUE[Message Queue]
        WORKER[Workers]
        ML[ML Pipeline]
    end
    
    subgraph "Storage"
        OLTP[(OLTP Database)]
        CACHE[(Redis Cache)]
        VECTOR[(Vector Database)]
        BLOB[Object Storage]
    end
    
    subgraph "Analytics"
        OLAP[(Analytics DB)]
        METRICS[Metrics Store]
        LOGS[Log Store]
    end
    
    API --> QUEUE
    WEBHOOK --> QUEUE
    UPLOAD --> BLOB
    
    QUEUE --> WORKER
    WORKER --> ML
    WORKER --> OLTP
    WORKER --> VECTOR
    
    OLTP --> CACHE
    OLTP --> OLAP
    WORKER --> METRICS
    WORKER --> LOGS
```

## Security Architecture

### Zero-Trust Security Model

```mermaid
graph TB
    subgraph "External Threats"
        THREAT[Threat Actors]
    end
    
    subgraph "Security Perimeter"
        WAF[Web Application Firewall]
        DDoS[DDoS Protection]
        CDN[CDN with Security]
    end
    
    subgraph "Authentication Layer"
        IDP[Identity Provider]
        MFA[Multi-Factor Auth]
        SSO[Single Sign-On]
    end
    
    subgraph "Authorization Layer"
        RBAC[Role-Based Access Control]
        ABAC[Attribute-Based Access Control]
        TENANT[Tenant Isolation]
    end
    
    subgraph "Application Security"
        SAST[Static Analysis]
        DAST[Dynamic Analysis]
        SCA[Dependency Scanning]
        SECRETS[Secret Management]
    end
    
    subgraph "Data Protection"
        ENCRYPT[Field Encryption]
        AUDIT[Audit Logging]
        BACKUP[Encrypted Backups]
        DLP[Data Loss Prevention]
    end
    
    THREAT --> WAF
    WAF --> DDoS
    DDoS --> CDN
    CDN --> IDP
    IDP --> MFA
    MFA --> SSO
    SSO --> RBAC
    RBAC --> ABAC
    ABAC --> TENANT
    TENANT --> SAST
    SAST --> DAST
    DAST --> SCA
    SCA --> SECRETS
    SECRETS --> ENCRYPT
    ENCRYPT --> AUDIT
    AUDIT --> BACKUP
    BACKUP --> DLP
```

### Security Controls Matrix

| Layer | Control | Implementation | Compliance |
|-------|---------|----------------|------------|
| **Network** | TLS 1.3 | Ingress Controller | SOC2, FedRAMP |
| **Identity** | WorkOS AuthKit | JWT + MFA | SOC2, HIPAA |
| **Access** | RBAC + ABAC | Custom middleware | SOC2, GDPR |
| **Data** | Field encryption | AES-256-GCM | HIPAA, GDPR |
| **Audit** | Comprehensive logging | Structured logs | All standards |
| **Secrets** | Vault integration | Kubernetes secrets | SOC2, FedRAMP |

## Deployment Architecture

### Kubernetes Architecture

```mermaid
graph TB
    subgraph "Production Cluster"
        subgraph "Ingress"
            NGINX[NGINX Ingress]
            CERT[Cert Manager]
        end
        
        subgraph "Application Namespaces"
            subgraph "websets-prod"
                API[API Gateway Pods]
                CORE[Core Service Pods]
                WORKER[Worker Pods]
                WEB[Web UI Pods]
            end
        end
        
        subgraph "Data Namespaces"
            subgraph "data-prod"
                PG[PostgreSQL Cluster]
                REDIS[Redis Cluster]
                QDRANT[Qdrant Cluster]
            end
        end
        
        subgraph "System Namespaces"
            subgraph "monitoring"
                PROM[Prometheus]
                GRAF[Grafana]
                ALERT[AlertManager]
            end
            
            subgraph "security"
                FALCO[Falco]
                OPA[Open Policy Agent]
            end
        end
    end
```

### Environment Strategy

| Environment | Purpose | Configuration | Deployment |
|-------------|---------|---------------|------------|
| **Development** | Feature development | Minimal resources | Auto-deploy on PR |
| **Staging** | Integration testing | Production-like | Auto-deploy on merge |
| **Production** | Live system | Full resources | Manual approval |

### Blue-Green Deployment

```mermaid
graph LR
    subgraph "Load Balancer"
        LB[Traffic Router]
    end
    
    subgraph "Blue Environment"
        BLUE_API[API v1.2.2]
        BLUE_WEB[Web v1.2.2]
        BLUE_DB[(Database)]
    end
    
    subgraph "Green Environment"
        GREEN_API[API v1.2.3]
        GREEN_WEB[Web v1.2.3]
        GREEN_DB[(Database)]
    end
    
    LB -->|100% Traffic| BLUE_API
    LB -->|100% Traffic| BLUE_WEB
    LB -.->|0% Traffic| GREEN_API
    LB -.->|0% Traffic| GREEN_WEB
    
    BLUE_DB --- GREEN_DB
```

## Observability Architecture

### Monitoring Stack

```mermaid
graph TB
    subgraph "Application Layer"
        APP[Applications]
        METRICS[Metrics Endpoint]
        LOGS[Structured Logs]
        TRACES[Distributed Traces]
    end
    
    subgraph "Collection Layer"
        PROM[Prometheus]
        FLUENTD[Fluentd]
        JAEGER[Jaeger]
    end
    
    subgraph "Storage Layer"
        TSDB[(Time Series DB)]
        ELASTIC[(Elasticsearch)]
        TRACE_DB[(Trace Storage)]
    end
    
    subgraph "Visualization Layer"
        GRAFANA[Grafana Dashboards]
        KIBANA[Kibana Logs]
        JAEGER_UI[Jaeger UI]
    end
    
    subgraph "Alerting Layer"
        ALERT[AlertManager]
        PAGER[PagerDuty]
        SLACK[Slack Notifications]
    end
    
    APP --> METRICS
    APP --> LOGS
    APP --> TRACES
    
    METRICS --> PROM
    LOGS --> FLUENTD
    TRACES --> JAEGER
    
    PROM --> TSDB
    FLUENTD --> ELASTIC
    JAEGER --> TRACE_DB
    
    TSDB --> GRAFANA
    ELASTIC --> KIBANA
    TRACE_DB --> JAEGER_UI
    
    GRAFANA --> ALERT
    ALERT --> PAGER
    ALERT --> SLACK
```

### Key Metrics & SLIs

| Category | Metric | Target | Alert Threshold |
|----------|--------|--------|-----------------|
| **Availability** | Uptime | 99.9% | <99.5% |
| **Performance** | P95 Latency | <500ms | >1000ms |
| **Throughput** | Requests/sec | >1000 | <500 |
| **Errors** | Error Rate | <0.1% | >1% |
| **Security** | Failed Auth | <1% | >5% |

## Compliance & Governance

### Compliance Framework

```mermaid
graph TB
    subgraph "Compliance Standards"
        SOC2[SOC2 Type II]
        HIPAA[HIPAA]
        GDPR[GDPR]
        FEDRAMP[FedRAMP]
    end
    
    subgraph "Technical Controls"
        ENCRYPT[Data Encryption]
        ACCESS[Access Controls]
        AUDIT[Audit Logging]
        BACKUP[Secure Backups]
    end
    
    subgraph "Operational Controls"
        POLICY[Security Policies]
        TRAINING[Staff Training]
        INCIDENT[Incident Response]
        REVIEW[Regular Reviews]
    end
    
    subgraph "Monitoring Controls"
        SCAN[Vulnerability Scanning]
        MONITOR[Continuous Monitoring]
        REPORT[Compliance Reporting]
        ASSESS[Risk Assessment]
    end
    
    SOC2 --> ENCRYPT
    SOC2 --> ACCESS
    SOC2 --> AUDIT
    
    HIPAA --> ENCRYPT
    HIPAA --> ACCESS
    HIPAA --> BACKUP
    
    GDPR --> AUDIT
    GDPR --> ACCESS
    GDPR --> POLICY
    
    FEDRAMP --> ENCRYPT
    FEDRAMP --> MONITOR
    FEDRAMP --> SCAN
```

### Data Governance

1. **Data Classification**: Public, Internal, Confidential, Restricted
2. **Data Retention**: Automated lifecycle management
3. **Data Portability**: GDPR-compliant export capabilities
4. **Data Deletion**: Right to erasure implementation
5. **Data Lineage**: Complete audit trail tracking

## Disaster Recovery

### Recovery Strategy

| Component | RTO | RPO | Strategy |
|-----------|-----|-----|----------|
| **Application** | 15 min | 5 min | Blue-green deployment |
| **Database** | 30 min | 1 min | Streaming replication |
| **File Storage** | 1 hour | 15 min | Cross-region replication |
| **Full System** | 4 hours | 1 hour | Multi-region failover |

### Backup Architecture

```mermaid
graph LR
    subgraph "Primary Region"
        PRIMARY[Primary Systems]
        PRIMARY_DB[(Primary Database)]
        PRIMARY_FILES[Primary Storage]
    end
    
    subgraph "Backup Systems"
        BACKUP_DB[(Backup Database)]
        BACKUP_FILES[Backup Storage]
        SNAPSHOTS[Point-in-time Snapshots]
    end
    
    subgraph "DR Region"
        DR[DR Systems]
        DR_DB[(DR Database)]
        DR_FILES[DR Storage]
    end
    
    PRIMARY_DB -->|Streaming Replication| BACKUP_DB
    PRIMARY_FILES -->|Continuous Sync| BACKUP_FILES
    PRIMARY_DB -->|Daily Snapshots| SNAPSHOTS
    
    BACKUP_DB -->|Cross-region Replication| DR_DB
    BACKUP_FILES -->|Cross-region Sync| DR_FILES
```

## Performance & Scalability

### Scaling Strategy

```mermaid
graph TB
    subgraph "Horizontal Scaling"
        HPA[Horizontal Pod Autoscaler]
        CLUSTER[Cluster Autoscaler]
        LOAD[Load Balancing]
    end
    
    subgraph "Vertical Scaling"
        VPA[Vertical Pod Autoscaler]
        RESOURCES[Resource Limits]
        QOS[Quality of Service]
    end
    
    subgraph "Data Scaling"
        SHARDING[Database Sharding]
        CACHING[Multi-layer Caching]
        CDN[Content Delivery Network]
    end
    
    subgraph "Performance Optimization"
        ASYNC[Async Processing]
        BATCH[Batch Operations]
        COMPRESSION[Data Compression]
    end
```

### Caching Strategy

1. **L1 Cache**: Application-level caching (Redis)
2. **L2 Cache**: Database query result caching
3. **L3 Cache**: CDN edge caching for static assets
4. **L4 Cache**: Browser caching with appropriate headers

## Technology Stack Summary

### Backend Technologies
- **Runtime**: Python 3.11+ with FastAPI framework
- **Database**: PostgreSQL 15+ with read replicas
- **Cache**: Redis 7+ with clustering
- **Vector DB**: Qdrant for ML/AI workloads
- **Message Queue**: Celery with Redis broker
- **Authentication**: WorkOS AuthKit integration

### Frontend Technologies
- **Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite with hot module replacement
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React Query + Context API
- **Testing**: Jest + React Testing Library

### Infrastructure Technologies
- **Container**: Docker with multi-stage builds
- **Orchestration**: Kubernetes 1.28+
- **Service Mesh**: Istio (optional)
- **Ingress**: NGINX Ingress Controller
- **Monitoring**: Prometheus + Grafana + AlertManager
- **Logging**: Fluentd + Elasticsearch + Kibana

### Security Technologies
- **SAST**: Semgrep, Bandit, ESLint security rules
- **DAST**: OWASP ZAP automated scanning
- **Container Security**: Trivy, Hadolint
- **Secret Management**: Kubernetes secrets + Vault
- **Compliance**: Automated compliance checking

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15  
**Owner**: Platform Architecture Team
