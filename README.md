# WebSet Miner

An autonomous LLM-powered system for discovering, extracting, and structuring public web data at scale.

## Features

- **LLM-Powered Planning**: Uses GPT-4/Claude to create intelligent data mining strategies
- **Autonomous Discovery**: Finds relevant websites based on natural language queries
- **Headless Crawling**: Playwright-based browser automation for full DOM capture
- **Zero-Shot Extraction**: Schema inference and data extraction without manual configuration
- **Dual Storage**: PostgreSQL for relational data + ChromaDB, Pinecone, Qdrant, or Weaviate for vector search
- **Secure API**: JWT authentication with role-based access control
- **Audit Logging**: All requests recorded in an immutable audit trail
- **Background Processing**: Celery + Redis for scalable job execution
- **Production Ready**: Docker containerization and monitoring capabilities

## Quick Start

For detailed onboarding instructions see [ONBOARDING.md](ONBOARDING.md).

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- OpenAI API key (required)
- Anthropic API key (optional)

### Setup

1. **Clone and setup the project:**
```bash
git clone <repository>
cd webset-miner
make setup
```

2. **Configure environment:**
```bash
# Copy the sample env file and adjust non-secret settings
cp .env.example .env
```
Seed Vault with secrets from `vault_secrets_template.json`.

You can also open the repository in a [Dev Container](.devcontainer/devcontainer.json) which will
run `make setup` automatically after creation.

3. **Start services:**
```bash
docker-compose up -d
```

4. **Run your first mining job:**
```bash
# Using the CLI script
python scripts/run_job.py "AI startups in Europe hiring ML engineers"

# Or using the API (after registering a user)
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "AI startups in Europe hiring ML engineers"}'
```

## Architecture

### Core Components

1. **Planner Agent** - Creates execution strategies from natural language prompts
2. **Discovery Agent** - Finds relevant URLs using LLM-powered search
3. **Browser Crawler** - Headless Playwright-based web scraping
4. **Schema Inference Agent** - Zero-shot data structure inference
5. **Storage Layer** - PostgreSQL + ChromaDB, Pinecone, Qdrant, or Weaviate vector database
6. **Job Orchestration** - Celery + Redis task queue
7. **API Server** - FastAPI with JWT authentication

### Data Flow

```
User Prompt → Planning → URL Discovery → Crawling → Schema Inference → Data Extraction → Storage
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Jobs
- `POST /jobs/` - Create new mining job
- `GET /jobs/` - List user's jobs
- `GET /jobs/{job_id}` - Get job details
- `DELETE /jobs/{job_id}` - Cancel job
- `POST /jobs/{job_id}/restart` - Restart failed job

### Datasets
- `GET /datasets/` - List user's datasets
- `GET /datasets/{id}` - Get dataset details
- `GET /datasets/{id}/records` - Get dataset records
- `POST /datasets/{id}/search` - Semantic search in dataset
- `GET /datasets/{id}/export` - Export dataset (JSON/CSV)

### Health
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health check

### OpenAPI Documentation

Generate a full OpenAPI specification by running:

```bash
python scripts/generate_openapi_spec.py
```

The spec is written to `openapi.json` and can be used with tooling such as
Swagger UI for interactive docs.

## Usage Examples

### 1. Login via Auth0
Use the hosted login page to obtain an access token. After logging in you can call the API with the returned token:
```bash
ACCESS_TOKEN="<your Auth0 access token>"
curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8000/v1/jobs/
```

### 2. Create Mining Jobs
```bash
# Job for finding AI companies
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "AI startups in Silicon Valley with recent funding"}'

# Job for finding research papers
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Recent machine learning research papers from top conferences"}'
```

### 3. Monitor Job Progress
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/jobs/JOB_ID"
```

### 4. Search Extracted Data
```bash
curl -X POST "http://localhost:8000/datasets/DATASET_ID/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "companies with Series A funding",
    "limit": 10,
    "threshold": 0.7
  }'
```

## Configuration

### Environment Variables

Secrets are stored in Vault using `vault_secrets_template.json`:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/webset_miner
JWT_SECRET_KEY=your_super_secret_jwt_key_here
AUTH0_DOMAIN=dev-your-domain.us.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=https://api.websets.local
AUTH0_ISSUER=https://dev-your-domain.us.auth0.com/
```

Non-secret configuration in `.env`:

```env
MAX_CONCURRENT_CRAWLS=5
REQUEST_DELAY_MS=1000
USER_AGENT=WebSetMiner/1.0
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Scaling Configuration

For production deployments, adjust these settings:

- `MAX_CONCURRENT_CRAWLS`: Number of simultaneous crawls
- Celery worker count: Scale based on CPU cores
- Database connection pool size
- Vector store dimensions and index type

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Linting
This project uses **pre-commit** with Ruff for formatting and linting.
Install the hooks and run them on all files before committing:

```bash
pip install pre-commit
pre-commit run --all-files
```

### Running Security Scans
Security scans run automatically in CI using **Bandit**, **Safety**, and **Trivy**.
The workflow executes on every push and on a weekly schedule so vulnerabilities
are caught even when the code is idle. Install the tools locally before pushing
changes:

```bash
# Install tools
pip install bandit safety

# Bandit static analysis
bandit -r app -x tests -lll

# Safety dependency vulnerability scan
safety check -r requirements.txt -r requirements-dev.txt

# Trivy filesystem scan (requires Docker)
docker run --rm -v $(pwd):/repo aquasec/trivy fs --severity CRITICAL /repo
```

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement the `execute()` method
3. Add agent to task pipeline in `mining_tasks.py`
4. Update API endpoints if needed

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Production Deployment

For HTTPS configuration and container hardening guidance see
[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

### Docker Production Build
```bash
# Build optimized image
docker build -t webset-miner:latest .

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webset-miner
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webset-miner
  template:
    metadata:
      labels:
        app: webset-miner
    spec:
      containers:
      - name: webset-miner
        image: webset-miner:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: webset-miner-secrets
              key: database-url
```

Full manifests with resource requests, limits, and security context can be found
in the `k8s/` directory. Use `scripts/blue_green_deploy.sh` to perform
blue/green rollouts between the `webset-miner-blue` and `webset-miner-green`
deployments.

## CI/CD Pipeline

Automated builds and deployments run via **GitHub Actions**. Docker
images are built and pushed to GitHub Container Registry on every push
to `main` or a tagged release. Each image is scanned with **Trivy** for
critical vulnerabilities. If no issues are found, the workflow deploys
the updated containers over SSH using `docker-compose`.

## Monitoring

### Health Checks
- `/health/` - Basic health check
- `/health/detailed` - Component status
- `/health/readiness` - Kubernetes readiness probe
- `/health/liveness` - Kubernetes liveness probe

### Logging
Structured logging with loguru:
```python
from loguru import logger
logger.info("Job started", job_id=job.id, user_id=user.id)
```

### Metrics
Monitor these key metrics:
- Job completion rate
- Crawl success rate
- Data extraction quality scores
- API response times
- Worker queue length

## Security

### Best Practices
- Always use HTTPS in production
- Rotate JWT secret keys regularly
- Implement rate limiting
- Validate all user inputs
- Use environment variables for secrets
- Regular security updates managed automatically via Dependabot
- Dependency review on pull requests prevents introducing vulnerable packages

### Rate Limiting
```python
# Add to FastAPI app
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/jobs/")
@limiter.limit("10/minute")
async def create_job(...):
    ...
```

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   playwright install chromium
   ```

2. **Celery workers not starting**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Check Celery logs
   celery -A app.tasks.celery_app worker --loglevel=debug
   ```

3. **Database connection errors**
   ```bash
   # Check PostgreSQL status
   docker-compose logs db
   ```

4. **LLM API rate limits**
   - Implement exponential backoff
   - Use different API keys for different environments
   - Monitor usage and billing

### Performance Optimization

1. **Crawling Performance**
   - Adjust `MAX_CONCURRENT_CRAWLS`
   - Increase `REQUEST_DELAY_MS` for respectful crawling
   - Use IP rotation for large-scale operations

2. **Vector Search Performance**
   - Use IVF index for large datasets
   - Adjust embedding dimensions
   - Implement proper indexing strategies

3. **Database Performance**
   - Add indexes for frequently queried fields
   - Use database connection pooling
   - Implement query optimization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## Roadmap

- [ ] Support for additional vector databases (Pinecone, Weaviate)
- [ ] Integration with more LLM providers
- [ ] Advanced data validation and cleaning
- [ ] Real-time job monitoring dashboard
- [ ] Support for authenticated websites
- [ ] Multi-language content support
- [ ] Advanced scheduling and automation features

## 🔐 Secure Secrets Management (HashiCorp Vault)

- All sensitive secrets (API keys, DB passwords) should be loaded from Vault, not .env or plaintext files.
- Set `VAULT_ADDR` and `VAULT_TOKEN` environment variables for the app.
- Use `app/secrets/vault.py` to fetch secrets at runtime.

Docker deployments can use [Docker secrets](secrets/README.md) to inject
credentials without storing them in the compose file. Place secret files in
`./secrets` and reference them in `docker-compose.yml`.

Example:
```python
from app.secrets.vault import VaultClient
vault = VaultClient()
openai_key = vault.get_secret("secret/data/websets", "openai_api_key")
```

## 🚀 MinIO Security Automation & Compliance
- All bucket policies and scripts are versioned and reviewed in git.
- CI/CD pipelines apply, audit, and rotate policies and secrets automatically.
- Vault integration ensures all credentials are rotated and injected securely.
- TLS, access logging, and firewall rules are enforced for MinIO.
- Audit logs and compliance guides are protected and archived.
- Minimal manual oversight required; all changes are traceable and self-healing.