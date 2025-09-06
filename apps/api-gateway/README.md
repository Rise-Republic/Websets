# WebSets API Gateway

FastAPI-based backend service providing the main API for the WebSets enterprise data mining platform.

## Architecture

- **Framework**: FastAPI with Python 3.13
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session storage and job queues
- **Authentication**: JWT + WorkOS integration
- **Background Jobs**: Celery with Redis broker
- **Vector Storage**: Qdrant/Weaviate for embeddings

## Development Setup

### Prerequisites
- Python 3.13+
- PostgreSQL 15+
- Redis 7+

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/websets

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Environment
ENVIRONMENT=development
```

## Docker Deployment

Multi-stage Docker build optimized for production:

```dockerfile
# Build stage - install dependencies
FROM python:3.13-slim AS build
# ... dependency installation

# Runtime stage - minimal image
FROM python:3.13-slim
# ... application files
```

### Container Configuration
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **User**: Non-root `appuser`

## API Endpoints

### Core Routes
- `GET /health` - Health check
- `POST /api/v1/auth/login` - Authentication
- `GET /api/v1/jobs/` - List mining jobs
- `POST /api/v1/jobs/` - Create mining job
- `GET /api/v1/datasets/` - List datasets

### Authentication
- JWT-based authentication
- WorkOS integration for enterprise SSO
- Role-based access control (RBAC)

## Database Schema

### Key Tables
- `users` - User accounts and profiles
- `jobs` - Data mining jobs
- `datasets` - Extracted datasets
- `audit_logs` - Security audit trail

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Security Features

- **CORS**: Configured for trusted origins only
- **Rate Limiting**: Per-user and global limits
- **Audit Logging**: All API calls logged
- **Input Validation**: Pydantic models
- **SQL Injection Protection**: SQLAlchemy ORM

## Monitoring & Observability

### Metrics
- Prometheus metrics collection
- Custom business metrics
- Performance monitoring

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking with context

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/api/v1/status
```

## Background Processing

### Celery Workers
- Data mining tasks
- Email notifications
- Report generation

### Job Queue Management
```bash
# Start worker
celery -A app.celery worker --loglevel=info

# Monitor tasks
celery -A app.celery flower
```

## Testing

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=app

# Run integration tests
pytest tests/integration/
```

## Performance

### Optimization Features
- Database connection pooling
- Redis caching
- Async request handling
- Background task processing

### Scaling Considerations
- Horizontal scaling with load balancer
- Database read replicas
- Redis clustering
- Celery worker scaling

## Troubleshooting

### Common Issues

1. **Database Connection**: Check DATABASE_URL and PostgreSQL status
2. **Redis Connection**: Verify Redis is running and accessible
3. **Authentication Errors**: Check JWT_SECRET_KEY and WorkOS config
4. **CORS Issues**: Verify allowed_origins in settings

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with auto-reload
uvicorn app.main:app --reload
```

### Logs
```bash
# Container logs
docker logs compose-api-gateway-1

# Application logs
tail -f logs/app.log
```
