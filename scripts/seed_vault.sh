#!/bin/bash
# Seed Vault with secrets from vault_secrets_template.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$SCRIPT_DIR/../vault_secrets_template.json"

if ! docker compose ps --services --filter status=running | grep -q '^vault$'; then
  echo "Vault container must be running" >&2
  exit 1
fi

echo "Seeding Vault with template secrets..."
docker compose exec -T vault sh -c 'vault login -no-print root >/dev/null && vault kv put secret/websets @-' < "$TEMPLATE_PATH"

echo "Vault seeded"
