#!/bin/bash
# Audit MinIO bucket policy and log changes for compliance
set -e

MINIO_ALIAS=${MINIO_ALIAS:-myminio}
MINIO_BUCKET=${MINIO_BUCKET:-websets-data}

mc policy info "$MINIO_ALIAS/$MINIO_BUCKET"
mc admin policy list "$MINIO_ALIAS"

# Log output for traceability
mc policy info "$MINIO_ALIAS/$MINIO_BUCKET" > ./app/storage/minio_policy_audit.log
mc admin policy list "$MINIO_ALIAS" >> ./app/storage/minio_policy_audit.log

echo "MinIO policy audit log updated at ./app/storage/minio_policy_audit.log."
