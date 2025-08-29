#!/bin/bash
# Rotate database password using Vault via Celery task helper
set -e
python3 - <<'PY'
from app.tasks.secret_rotation import rotate_database_password
if not rotate_database_password():
    raise SystemExit("Database password rotation failed")
PY
echo "Database password rotated via Vault."
