#!/bin/bash
# Rotate JWT secret key using Vault via Celery task helper
set -e
python3 - <<'PY'
from app.tasks.secret_rotation import rotate_jwt_secret
if not rotate_jwt_secret():
    raise SystemExit("JWT secret rotation failed")
PY
echo "JWT secret rotated via Vault."
