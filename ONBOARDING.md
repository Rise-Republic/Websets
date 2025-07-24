# Developer Onboarding

Follow these steps to get a local environment running quickly.

> **Important**
> The repository history was rewritten to remove sensitive data. If you cloned
> the project before this rewrite, delete your old copy and clone it again.
> After cloning, run `make setup` to reinstall all dependencies.

## 1. Clone and Setup

```bash
git clone <repository>
cd webset-miner
make setup
```

The `setup` target installs Python and Node **dev** dependencies, sets up Playwright, and creates an `.env` file from `.env.example` if needed.

## 2. Configure Secrets

Load all sensitive secrets into Vault using `vault_secrets_template.json`. The `.env` file only contains non-secret settings.

## 3. Start Services

```bash
docker-compose up -d
```

## 4. Run a Test Job

```bash
python scripts/run_job.py "AI startups in Silicon Valley"
```

## 5. Run Tests

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
