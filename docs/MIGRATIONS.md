# Database Migrations

Database schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Migration scripts live in `migrations/versions`.

## Workflow

1. Make model changes under `app/models`.
2. Create a new revision:
   ```bash
   DB_URL=$DATABASE_URL alembic revision --autogenerate -m "Add user table"
   ```
   Review the generated file in `migrations/versions/` and adjust if needed.
3. Apply migrations:
   ```bash
DB_URL=$DATABASE_URL alembic upgrade head
   ```
   `DB_URL` should point to your target database URL and mirrors the value used
   for `DATABASE_URL`.
4. If a migration needs to be reverted:
   ```bash
   alembic downgrade -1
   ```

## Versioning Guidelines

- Use descriptive messages (e.g. "add_index_to_jobs") in lowercase.
- Revisions are ordered by timestamp prefix; do not edit existing revisions once pushed.
- Keep migrations idempotent. Avoid data‑destructive operations in `upgrade()` unless absolutely necessary.

