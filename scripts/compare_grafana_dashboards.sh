#!/bin/bash
# Compare committed dashboard JSON with live Grafana dashboards
set -euo pipefail

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASS=${GRAFANA_PASS:-admin}

diff_found=0

dashboard_dir="monitoring/grafana/dashboards"

for file in "$dashboard_dir"/*.json; do
  name=$(basename "$file" .json)
  api_url="$GRAFANA_URL/api/dashboards/db/$name"
  live_json=$(curl -sf -u "$GRAFANA_USER:$GRAFANA_PASS" "$api_url" | jq -S '.dashboard') || {
    echo "Failed to fetch dashboard $name" >&2
    diff_found=1
    continue
  }
  local_json=$(jq -S '.' "$file")
  if ! diff -u <(echo "$local_json") <(echo "$live_json"); then
    echo "Dashboard drift detected for $file" >&2
    diff_found=1
  fi
 done

exit $diff_found
