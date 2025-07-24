# Contributing Guide

This project welcomes community contributions. Please follow the rules below to help keep the repository consistent and easy to maintain.

## Contribution Workflow

1. Fork the repository and create your feature branch from `develop`.
2. Name branches using `feature/<short-description>` or `bugfix/<issue-number>`.
3. Commit logically separated changes with clear messages.
4. Open a pull request against `develop` and ensure the CI checks pass.
5. A maintainer will review and merge after approval.

## Branching Strategy

- **main** – stable production branch.
- **develop** – integration branch for day-to-day work.
- **feature/*** – new features based off `develop`. Merge back via pull request.
- **release/*** – release preparation branches cut from `develop`. Merge into `main` when ready and tag with `vX.Y.Z`.
- **hotfix/*** – critical fixes based off `main`. Merge back into both `main` and `develop`.

All changes should go through a pull request with a passing CI run.

## Commit Style

- Use the _imperative mood_ (e.g. "Add logging" not "Added logging").
- Keep the summary under **50 characters**.
- Include a body if the change is non‑trivial. Wrap lines at 72 characters.
- Reference related issues using `#123` where appropriate.

## Testing Rules

- New code requires tests. Update existing tests when behavior changes.
- Run `pre-commit run --all-files`, `make fmt`, `make lint`, and `make test` before opening a pull request.
- Run `mypy --strict` to check types with the configuration in `mypy.ini`.
- Fix any linter errors and ensure all tests pass locally.

### Local CI

Run the same checks as the GitHub Actions workflow:

```bash
pre-commit run --all-files
bash scripts/ci-run.sh
```

## Code Review Checklist

Reviewers verify:

- [ ] Code follows style guidelines and includes type hints
- [ ] Security-sensitive code has been audited
- [ ] Performance impact is considered
- [ ] Tests cover new functionality and pass locally

Following these guidelines keeps the history readable and the CI pipeline green. Thank you for contributing!
