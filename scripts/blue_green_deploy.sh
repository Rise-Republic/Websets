#!/bin/bash
# Simple blue/green deployment script for Kubernetes

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

# Apply the chosen deployment and wait for rollout
kubectl apply -f k8s/deployment-$COLOR.yaml
kubectl rollout status deployment/$DEPLOYMENT

# Update service selector to route traffic
kubectl patch service webset-miner -p '{"spec":{"selector":{"app":"'$DEPLOYMENT'"}}}'

echo "Switched service to $DEPLOYMENT"
