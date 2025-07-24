#!/bin/bash
# Generate self-signed CA and service certificates for mTLS
set -e
CERT_DIR=${1:-certs}
mkdir -p "$CERT_DIR"

# Create CA
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 \
  -nodes -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \
  -subj "/CN=websets-ca"
chmod 600 "$CERT_DIR/ca.key"

SERVICES=(app minio vault redis qdrant weaviate prometheus)

for svc in "${SERVICES[@]}"; do
  openssl req -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/${svc}.key" -out "$CERT_DIR/${svc}.csr" \
    -subj "/CN=${svc}"
  openssl x509 -req -in "$CERT_DIR/${svc}.csr" \
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
    -out "$CERT_DIR/${svc}.crt" -days 365 -sha256
  rm "$CERT_DIR/${svc}.csr"
  chmod 600 "$CERT_DIR/${svc}.key"
done

echo "mTLS certificates generated in $CERT_DIR"
