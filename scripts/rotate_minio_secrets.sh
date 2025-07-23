#!/bin/bash
# Rotate MinIO credentials and store them in Vault
set -e

NEW_ACCESS_KEY=$(openssl rand -hex 16)
NEW_SECRET_KEY=$(openssl rand -hex 32)

export MINIO_ACCESS_KEY="$NEW_ACCESS_KEY"
export MINIO_SECRET_KEY="$NEW_SECRET_KEY"

VAULT_ADDR=${VAULT_ADDR:?}
VAULT_TOKEN=${VAULT_TOKEN:?}
VAULT_SECRET_PATH=${MINIO_VAULT_PATH:-secret/websets}

API_PATH=${VAULT_SECRET_PATH#secret/}
PAYLOAD=$(jq -n --arg ak "$NEW_ACCESS_KEY" --arg sk "$NEW_SECRET_KEY" '{data:{MINIO_ACCESS_KEY:$ak, MINIO_SECRET_KEY:$sk}}')

curl -sS --header "X-Vault-Token: $VAULT_TOKEN" --request POST \
    --data "$PAYLOAD" "$VAULT_ADDR/v1/secret/data/$API_PATH"

echo "MinIO credentials rotated and stored in Vault at $VAULT_SECRET_PATH."
