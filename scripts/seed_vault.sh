#!/bin/bash
# Seed Vault with secrets from vault_secrets_template.json
set -euo pipefail

if ! docker compose ps --services --filter status=running | grep -q '^vault$'; then
  echo "Vault container must be running" >&2
  exit 1
fi

echo "Seeding Vault with template secrets..."
docker compose exec -T vault sh -c 'vault login -no-print root >/dev/null && vault kv put secret/websets @-' < vault_secrets_template.json

echo "Vault seeded"
