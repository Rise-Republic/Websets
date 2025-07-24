#!/bin/bash
# Rotate MinIO credentials using the Python helper and export them
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT=$(python3 "$SCRIPT_DIR/rotate_minio_secrets.py")
# shellcheck disable=SC1090
eval "$OUTPUT"

echo "MinIO credentials rotated via Vault."
