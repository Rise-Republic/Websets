# Start Here

Follow these steps to set up WebSet Miner quickly.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- OpenAI API key (required)
- Anthropic API key (optional)

## One‑Command Setup

Run the `make dev` command after cloning the repository:

```bash
make dev
```

This installs all dependencies, generates certificates, seeds Vault, applies migrations, and launches the Docker Compose stack. A `.env` file is created automatically from `.env.example` if needed.

## Next Steps

1. Launch a sample job:
   ```bash
   python scripts/run_job.py "AI startups in Silicon Valley"
   ```

For more information see [ONBOARDING.md](../ONBOARDING.md).
