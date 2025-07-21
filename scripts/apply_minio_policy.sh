#!/bin/bash
# Apply MinIO bucket policy for encryption enforcement
set -e

MINIO_ALIAS=${MINIO_ALIAS:-myminio}
MINIO_URL=${MINIO_URL:-http://localhost:9000}
MINIO_USER=${MINIO_USER:-minioadmin}
MINIO_PASS=${MINIO_PASS:-minioadmin}
MINIO_BUCKET=${MINIO_BUCKET:-websets-data}
POLICY_PATH=./app/storage/minio_policy.json

mc alias set "$MINIO_ALIAS" "$MINIO_URL" "$MINIO_USER" "$MINIO_PASS"
mc admin policy add "$MINIO_ALIAS" force-encryption "$POLICY_PATH"
mc admin policy set "$MINIO_ALIAS" force-encryption user="$MINIO_USER"
mc policy set "$MINIO_ALIAS/$MINIO_BUCKET" force-encryption

echo "MinIO encryption policy applied to $MINIO_BUCKET."
