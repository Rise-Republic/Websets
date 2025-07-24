# Database Migrations

Database schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Migration scripts live in `migrations/versions`.

## Workflow

1. Make model changes under `app/models`.
2. Create a new revision:
   ```bash
   alembic revision --autogenerate -m "Add user table"
   ```
   Review the generated file in `migrations/versions/` and adjust if needed.
3. Apply migrations:
   ```bash
   alembic upgrade head
   ```
4. If a migration needs to be reverted:
   ```bash
   alembic downgrade -1
   ```

## Versioning Guidelines

- Use descriptive messages (e.g. "add_index_to_jobs") in lowercase.
- Revisions are ordered by timestamp prefix; do not edit existing revisions once pushed.
- Keep migrations idempotent. Avoid data‑destructive operations in `upgrade()` unless absolutely necessary.

