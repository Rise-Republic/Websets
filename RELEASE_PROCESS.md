# Release Process

This project uses a simple Git workflow with protected branches and
SemVer tags. Follow these guidelines when preparing a release.

## Branch Cleanup
- Delete stale branches (e.g. `work`) after they are merged.
- Keep the repository tidy so branch names do not accumulate.

## Protected Branches
- The `main` branch must remain protected.
- Release preparation occurs in branches matching `release/*`.
- Only maintainers may merge to `main` or create release branches.

## Tagging
- When a release is ready, tag the merge commit on `main` using
  `vX.Y.Z` semantics (e.g. `v1.2.0`).
- Tags trigger Docker image builds and deployments via CI/CD.

Following these steps ensures consistent Docker deployments and a clean
history.
