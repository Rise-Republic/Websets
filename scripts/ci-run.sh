#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
HEALTH_TIMEOUT=${HEALTH_TIMEOUT:-300}
CHECK_INTERVAL=5

cleanup() {
  echo "Tearing down services..."
  docker-compose -f "$COMPOSE_FILE" down --volumes
}
trap cleanup EXIT

echo "Building and starting services..."
docker-compose -f "$COMPOSE_FILE" up --build -d

services=$(docker-compose -f "$COMPOSE_FILE" ps --services)
for svc in $services; do
  cid=$(docker-compose -f "$COMPOSE_FILE" ps -q $svc)
  echo "Waiting for $svc to be healthy..."
  elapsed=0
  status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid")
  until [[ "$status" == "healthy" || "$status" == "running" ]]; do
    if [[ $elapsed -ge $HEALTH_TIMEOUT ]]; then
      echo "$svc did not become healthy within $HEALTH_TIMEOUT seconds"
      docker-compose -f "$COMPOSE_FILE" logs $svc
      exit 1
    fi
    sleep $CHECK_INTERVAL
    elapsed=$((elapsed + CHECK_INTERVAL))
    status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid")
  done
  echo "$svc is $status"
done

# Install dependencies in case running locally without workflow
if [ -f requirements.txt ]; then
  pip install -r requirements.txt -r requirements-dev.txt
fi
if [ -f package.json ]; then
  npm ci
fi

echo "Running static analysis..."
ruff .
mypy .

echo "Running backend tests..."
pytest --maxfail=1 --disable-warnings -q

echo "Running frontend tests..."
npm test -- --runInBand
npm run build

echo "CI run completed successfully."
