# Penetration Tester's Guide

## Architecture Overview
- FastAPI backend with PostgreSQL and Redis.
- React/TypeScript frontend served as static assets.
- All services run in Kubernetes with network policies and HPAs.

## Services & Endpoints
- API: `POST /v1/auth/login`, `GET /v1/datasets`, `GET /health`.
- Static content served from `/`.

## AuthN/AuthZ
- JWT bearer tokens with tenant-aware RBAC.
- Session middleware for WorkOS OIDC.

## Test Environment Setup
1. `docker-compose up` (local) or use provided Kubernetes manifests in `k8s/`.
2. Seed database with test tenant and user.
3. Use `.env.example` as reference for required secrets.

## Notes for Testers
- Each request must include `X-Org-ID` header matching JWT claim.
- RLS enforces tenant isolation; attempts to cross-tenant access should fail.
- Alertmanager at `http://localhost:9093` for observing triggered alerts.
