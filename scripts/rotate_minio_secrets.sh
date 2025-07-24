#!/bin/bash
# Rotate MinIO credentials and update environment securely
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT=$(python "$SCRIPT_DIR/rotate_minio_secrets.py")
NEW_ACCESS_KEY=$(echo "$OUTPUT" | grep MINIO_ACCESS_KEY | cut -d= -f2)
NEW_SECRET_KEY=$(echo "$OUTPUT" | grep MINIO_SECRET_KEY | cut -d= -f2)

export MINIO_ACCESS_KEY="$NEW_ACCESS_KEY"
export MINIO_SECRET_KEY="$NEW_SECRET_KEY"

echo "MinIO credentials rotated in Vault and exported."
