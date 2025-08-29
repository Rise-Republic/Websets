#!/bin/bash
# Rotate API keys using Vault via Celery task helper
set -e
python3 - <<'PY'
from app.tasks.secret_rotation import rotate_api_keys
if not rotate_api_keys():
    raise SystemExit("API key rotation failed")
PY
echo "API keys rotated via Vault."
