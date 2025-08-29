#!/usr/bin/env bash
set -euo pipefail

TENANT="${TENANT:?TENANT environment variable required}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PUSHGATEWAY_URL="${PUSHGATEWAY_URL:-http://localhost:9091}"
BASE_URL="${BASE_URL:-https://${ENVIRONMENT}.example.com}"
ENDPOINTS="${ENDPOINTS:-/api/health /api/v1/datasets}"

probe() {
  local endpoint="$1"
  local url="$BASE_URL$endpoint"
  local start
  start=$(date +%s%3N)
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Org-ID: $TENANT" "$url")
  local elapsed
  elapsed=$(($(date +%s%3N) - start))
  local status=0
  if [[ "$code" -ge 200 && "$code" -lt 400 ]]; then
    status=1
  fi
  cat <<METRICS | curl --data-binary @- "$PUSHGATEWAY_URL/metrics/job/synthetics/tenant/$TENANT/env/$ENVIRONMENT"
synthetic_probe_status{endpoint="$endpoint"} $status
synthetic_probe_latency_ms{endpoint="$endpoint"} $elapsed
METRICS
}

for ep in $ENDPOINTS; do
  probe "$ep"
done
