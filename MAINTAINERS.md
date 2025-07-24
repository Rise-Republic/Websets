# Maintainers Guide

This document outlines the branch strategy and general maintenance rules for the project.

## Branch Strategy

- **main**: stable branch deployed to production. Only merge via pull request.
- **develop**: integration branch for day-to-day work. Feature branches should be based off `develop` and merged back through pull requests.
- **release/***: temporary branches cut from `develop` when preparing a release. After testing, merge into `main` and tag.
- **hotfix/***: critical fixes based off `main` and merged back into both `main` and `develop`.

All changes require a pull request with passing CI checks.

## Maintenance Guidelines

1. Keep dependencies up to date. Run `make setup` after pulling new requirements.
2. Run `pre-commit run --all-files` before pushing to ensure formatting and linting.
3. Ensure `pytest` and `npm test` pass locally.
4. Document notable changes in `CHANGELOG.md` (create the file if it does not exist).
5. Avoid committing secrets or personal data; use Vault and `.env.example` for configuration templates.

