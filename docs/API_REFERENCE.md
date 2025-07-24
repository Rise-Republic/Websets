# API Reference

This document summarizes the primary REST endpoints exposed by the FastAPI application. All routes are served under `http://localhost:8000` when running locally.

## Authentication

| Method | Path | Description |
|-------|------|-------------|
|POST|`/v1/auth/register`|Register new user|
|POST|`/v1/auth/login`|Login and obtain JWT tokens|
|POST|`/v1/auth/mfa/setup`|Enable TOTP multi-factor authentication|
|POST|`/v1/auth/mfa/verify`|Verify MFA code and obtain tokens|
|POST|`/v1/auth/refresh`|Refresh access token|
|POST|`/v1/auth/password-reset/request`|Send password reset email|
|POST|`/v1/auth/password-reset/confirm`|Confirm new password|
|GET|`/v1/auth/me`|Current user profile|

## Jobs

| Method | Path | Description |
|-------|------|-------------|
|POST|`/jobs/`|Create new mining job|
|GET|`/jobs/`|List jobs|
|GET|`/jobs/{job_id}`|Get job details|
|DELETE|`/jobs/{job_id}`|Cancel running job|
|POST|`/jobs/{job_id}/restart`|Restart failed job|

## Datasets

| Method | Path | Description |
|-------|------|-------------|
|GET|`/datasets/`|List datasets|
|GET|`/datasets/{id}`|Dataset details|
|GET|`/datasets/{id}/records`|List records|
|POST|`/datasets/{id}/search`|Semantic search|
|GET|`/datasets/{id}/export`|Export dataset|
|DELETE|`/datasets/{id}`|Delete dataset|

## Health

| Method | Path | Description |
|-------|------|-------------|
|GET|`/health/`|Basic health check|
|GET|`/health/detailed`|Detailed component status|
|GET|`/health/readiness`|Kubernetes readiness probe|
|GET|`/health/liveness`|Kubernetes liveness probe|
|GET|`/health/metrics`|Prometheus metrics|

## Example Request

```bash
curl -X POST http://localhost:8000/jobs/ \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "AI startups in Europe"}'
```

The response schema for a job is shown below (truncated):

```json
{
  "id": "6f8e2...",
  "prompt": "AI startups in Europe",
  "status": "PENDING",
  "created_at": "2025-07-24T12:34:56Z",
  "plan": {}
}
```

## Error Codes

| Status | Meaning | Retry Guidance |
|-------|---------|----------------|
|400|Bad request|Check request body and parameters|
|401|Unauthorized|Refresh token or login again|
|404|Not found|Verify resource identifier|
|429|Rate limited|Wait and retry with exponential backoff|
|500|Server error|Retry later; investigate server logs|

