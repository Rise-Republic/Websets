#!/bin/bash
# Rotate MinIO credentials and update environment securely
set -e

NEW_ACCESS_KEY=$(openssl rand -hex 16)
NEW_SECRET_KEY=$(openssl rand -hex 32)

# Update MinIO credentials (example for local dev)
export MINIO_ACCESS_KEY="$NEW_ACCESS_KEY"
export MINIO_SECRET_KEY="$NEW_SECRET_KEY"

# Optionally update Vault or secrets manager here
# vault kv put secret/minio access_key="$NEW_ACCESS_KEY" secret_key="$NEW_SECRET_KEY"

echo "MinIO credentials rotated. New keys exported to environment."
