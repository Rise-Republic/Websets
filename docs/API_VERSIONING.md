# API Versioning Strategy

WebSet Miner exposes REST endpoints under versioned prefixes (e.g. `/v1`). This document explains how
new API versions will be introduced and how breaking changes are handled.

## Semantic Versioning

The project follows [Semantic Versioning](https://semver.org/). Patch and minor releases never remove
existing fields or change request/response formats in a backward‑incompatible way.
Breaking changes are reserved for new **major** versions.

## URL Prefixes

Each major version is exposed under its own URL prefix:

- `v1` – Initial stable release.
- Future versions will use `/v2`, `/v3`, and so on.

Old versions remain available for at least **one release cycle** after a new major version is published.
Client applications should migrate during this window.

## Deprecation Process

1. A new major version is released under a new prefix.
2. The previous version is marked as deprecated in the `/api/versions` endpoint and in response headers.
3. Deprecated versions continue to function for a minimum of six months.
4. After the deprecation period, the version is removed from the deployment.

## Specifying a Version

Clients select an API version by either:

- Including the version prefix in the URL (`/v1/jobs/`).
- Sending an `API-Version` header (e.g. `API-Version: v1`).
- Using an `Accept` header such as `application/vnd.websetminer.v1+json`.

If no version is specified, the server defaults to the current stable version.

## Compatibility Guarantees

Within a major version, endpoints and field names remain stable. New optional fields may be added, but
existing behavior will not change in a breaking manner. When incompatible updates are necessary, a new
major version is introduced following the process above.
