# Contributing Guide

This project welcomes community contributions. Please follow the rules below to help keep the repository consistent and easy to maintain.

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

Following these guidelines keeps the history readable and the CI pipeline green. Thank you for contributing!
