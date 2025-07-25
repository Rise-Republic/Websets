# WebSet Miner

WebSet Miner is an autonomous system for discovering and extracting public web data using large language models. It combines a Python FastAPI backend with a React/TypeScript frontend and a Celery worker pool for background tasks. Data is stored in PostgreSQL and a pluggable vector database.

## Architecture

```
User → FastAPI → Celery Workers → Agents → Storage
```

- **FastAPI** – REST API and WebSocket server
- **Celery** – Background job processing using Redis
- **Agents** – Planner, discovery crawler, schema inference
- **Playwright** – Headless browser automation
- **PostgreSQL** – Primary relational storage
- **Vector DB** – ChromaDB, Pinecone, Qdrant or Weaviate
- **React** – Frontend built with Vite

## Local Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node 20+
- OpenAI API key (required)

### Steps
1. Clone the repository
   ```bash
   git clone <repo-url>
   cd Websets
   ```
2. Copy `.env.example` to `.env` and adjust values. Set `DISABLE_VAULT_FOR_LOCAL_DEV=true` for local development.
3. Start the full stack
   ```bash
   make dev
   ```
   This installs dependencies, applies migrations and starts all services with Docker Compose.
4. Access the API at `http://localhost:8001` and the docs at `http://localhost:8001/docs`.
5. In another terminal start the frontend
   ```bash
   npm install
   npm run dev
   ```

## Running Tests

```bash
# Backend tests
pytest

# Frontend tests
npm test
```

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
