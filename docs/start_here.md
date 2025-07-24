# Start Here

Follow these steps to set up WebSet Miner quickly.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- OpenAI API key (required)
- Anthropic API key (optional)

## One‑Command Setup

Run the `make setup` command after cloning the repository:

```bash
make setup
```

This executes `scripts/setup.sh`, which installs Python and Node dependencies, installs Playwright browsers, and creates a `.env` file from `.env.example` if it does not exist.

## Next Steps

1. Fill in your API keys and other values in `.env`. Supply `VAULT_TOKEN` separately via an environment variable or Docker secret since it is not included in `.env.example`.
2. Start the services:
   ```bash
   docker compose up -d
   ```
3. Launch a sample job:
   ```bash
   python scripts/run_job.py "AI startups in Silicon Valley"
   ```

For more information see [ONBOARDING.md](../ONBOARDING.md).
