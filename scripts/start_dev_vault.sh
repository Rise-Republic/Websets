#!/bin/bash
# Start a local Vault dev server and seed it with template secrets
set -e

VAULT_TOKEN=${VAULT_TOKEN:-root}
VAULT_ADDR=${VAULT_ADDR:-http://127.0.0.1:8200}
VAULT_SECRET_PATH=${VAULT_SECRET_PATH:-secret/websets}

docker run -d --name dev-vault --cap-add=IPC_LOCK \
  -e VAULT_DEV_ROOT_TOKEN_ID=$VAULT_TOKEN \
  -e VAULT_DEV_LISTEN_ADDRESS="0.0.0.0:8200" \
  -p 8200:8200 hashicorp/vault:1.14 >/dev/null

sleep 5

python scripts/seed_vault.py

echo "Vault dev server running at $VAULT_ADDR"
