# WebSet Miner

WebSet Miner is an autonomous system for discovering and extracting public web data using large language models. It combines a Python FastAPI backend with a React/TypeScript frontend and a Celery worker pool for background tasks. Data is stored in PostgreSQL and a pluggable vector database.

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
- `POST /v1/auth/register`  Register new user
- `GET /v1/auth/verify-email`  Confirm email address *(planned)*
- `POST /v1/auth/login`  Login and obtain access + refresh tokens (returns 202 with `X-MFA-Required` when MFA is enabled)_
- `POST /v1/auth/mfa/setup`  Enable TOTP MFA and receive a secret key
- `POST /v1/auth/mfa/verify`  Verify MFA challenge and obtain tokens
- `POST /v1/auth/refresh`  Refresh expired access token
- `POST /v1/auth/password-reset/request`  Send password reset link
- `POST /v1/auth/password-reset/confirm`  Confirm new password
- `GET /v1/auth/me`  Get current user info

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

### 1. Login via WorkOS AuthKit
Open the app and click **Sign in with AuthKit**. After authenticating you will be redirected back with a session cookie already set. You can then call the API directly:
```bash
curl -b cookie.txt -c cookie.txt http://localhost:8001/api/auth/me
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
@@ -296,53 +295,51 @@ new fixture:
2. Use `yield` fixtures if cleanup is required after the test.
3. Patch network calls or environment variables to avoid hitting real services.
4. Reuse existing fixtures where possible to speed up tests.

### Linting
This project uses **pre-commit** with Ruff for formatting and linting.
Install the hooks with `pre-commit install` and run them on all files before committing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Frontend Development

The React UI resides in the `src/` directory and uses Vite. Install dependencies and launch the dev server with:

```bash
npm install
npm run dev
```

Set these environment variables locally:

- `VITE_WORKOS_CLIENT_ID` – WorkOS client ID
- `VITE_API_BASE` – backend URL override (optional)

Build the production bundle:

```bash
npm run build
```

Run frontend tests with:

```bash
npm test
```

### Editor Configuration
The repository defines basic formatting rules in [.editorconfig](.editorconfig). Python files use 4-space indents while the frontend code under `src/` uses 2 spaces. Most editors will pick up these settings automatically and ensure newlines end with `LF`.

### Running Security Scans
Security scans run automatically in CI using **Bandit**, **Safety**, and **Trivy**.
The workflow executes on every push and on a weekly schedule so vulnerabilities
are caught even when the code is idle. Install the tools locally before pushing
changes:

```bash
# Install tools

## Building for Production

Use the provided multi‑stage `Dockerfile` to create a production image:

```bash
docker build -t webset-miner .
```

The build stage installs Python and Node dependencies and compiles the frontend. The final image contains only the runtime environment and compiled assets.

## Repository Layout

```
app/       – FastAPI application
src/       – React frontend
migrations/ – Alembic database migrations
scripts/   – Utility scripts
tests/     – Test suite
```

## License

This project is released under the MIT License.