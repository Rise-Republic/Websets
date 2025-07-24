#!/bin/bash
# Blue/green deployment script for Kubernetes.
# It waits for the new deployment to be ready and checks key Prometheus metrics.
# If metrics remain unhealthy within a timeout the script reverts traffic to the
# previous deployment.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <blue|green>" >&2
  exit 1
fi

COLOR=$1
if [[ "$COLOR" != "blue" && "$COLOR" != "green" ]]; then
  echo "Color must be 'blue' or 'green'" >&2
  exit 1
fi

DEPLOYMENT="webset-miner-$COLOR"
CURRENT_SELECTOR=$(kubectl get service webset-miner -o jsonpath='{.spec.selector.app}')

PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:9090}
DEPLOY_TIMEOUT=${DEPLOY_TIMEOUT:-120s}
HEALTH_TIMEOUT=${HEALTH_TIMEOUT:-60}
ERROR_RATE_THRESHOLD=${ERROR_RATE_THRESHOLD:-0.05}

kubectl apply -f k8s/deployment-$COLOR.yaml
if ! kubectl rollout status deployment/$DEPLOYMENT --timeout="$DEPLOY_TIMEOUT"; then
  echo "Rollout of $DEPLOYMENT failed" >&2
  exit 1
fi

# Switch service to the new deployment
kubectl patch service webset-miner -p '{"spec":{"selector":{"app":"'$DEPLOYMENT'"}}}'

check_metrics() {
  local result
  result=$(curl -sf "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=rate(websets_http_requests_total{status_code!~\"2..\"}[1m]) / rate(websets_http_requests_total[1m])" \
    | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "1")
  awk 'BEGIN{exit !("'"$result"'" < "'"$ERROR_RATE_THRESHOLD"'")}'
}

echo "Monitoring new deployment metrics..."
end=$(( $(date +%s) + HEALTH_TIMEOUT ))
while [ $(date +%s) -lt $end ]; do
  if check_metrics; then
    echo "Deployment healthy. Switched service to $DEPLOYMENT"
    exit 0
  fi
  sleep 5
done

echo "Metrics check failed. Reverting to $CURRENT_SELECTOR..." >&2
kubectl patch service webset-miner -p '{"spec":{"selector":{"app":"'$CURRENT_SELECTOR'"}}}'
exit 1
