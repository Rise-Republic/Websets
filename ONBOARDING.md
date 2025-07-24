# Developer Onboarding

Follow these steps to get a local environment running quickly.

> **Important**
> The repository history was rewritten to remove sensitive data. If you cloned
> the project before this rewrite, delete your old copy and clone it again.
> After cloning, run `make dev` to launch the stack and install all dependencies.

## 1. Clone and Start the Stack

```bash
git clone <repository>
cd webset-miner
make dev
```

This command installs dependencies, generates certificates, seeds Vault, configures a default `DATABASE_URL` and disables Vault for local use, then applies migrations and launches all services. A `.env` file is created automatically if it does not exist.

## 2. Run a Test Job

```bash
python scripts/run_job.py "AI startups in Silicon Valley"
```

## 3. Run Tests

Run backend tests with **pytest** and frontend tests with **Jest**:

```bash
# Backend
pytest

# Frontend
npm test
```

## Troubleshooting

- **Playwright browser not found**: `playwright install chromium`
- **Celery workers not starting**: check Redis connection and Celery logs
- **Database connection errors**: `docker-compose logs db`
- **LLM API rate limits**: implement backoff and monitor usage

For more details see the `README.md` troubleshooting section.
