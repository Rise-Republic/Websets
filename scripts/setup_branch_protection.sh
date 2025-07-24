#!/usr/bin/env bash
# Configure branch protection rules using GitHub CLI
set -euo pipefail

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

main_branches=("main" "release/*")

for branch in "${main_branches[@]}"; do
  gh api -X PUT repos/$REPO/branches/${branch//\/*}/protection \
    -F required_status_checks.strict=true \
    -F required_status_checks.contexts='["lint-format","tests","security"]' \
    -F enforce_admins=true \
    -F required_pull_request_reviews.dismiss_stale_reviews=true \
    -F required_pull_request_reviews.required_approving_review_count=2 \
    -F allow_force_pushes=false \
    -F deletions=false \
    -F required_signatures=true
done

echo "Feature branches should require a passing workflow run and be up to date with main. Configure via GitHub UI or gh CLI accordingly."
