"""Make tenant_id columns non-null with defaults"""

from alembic import op
import sqlalchemy as sa

revision = "tenant_id_non_null_20250915"
down_revision = "add_verification_fields_20250906"
branch_labels = None
depends_on = None


def upgrade():
    tables = [
        "users",
        "jobs",
        "datasets",
        "data_records",
        "discovered_urls",
        "crawl_results",
        "audit_logs",
        "data_access_logs",
    ]
    for table in tables:
        op.execute(
            sa.text(
                f"UPDATE {table} SET tenant_id = gen_random_uuid() WHERE tenant_id IS NULL"
            )
        )
        op.alter_column(
            table,
            "tenant_id",
            existing_type=sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        )


def downgrade():
    tables = [
        "data_access_logs",
        "audit_logs",
        "crawl_results",
        "discovered_urls",
        "data_records",
        "datasets",
        "jobs",
        "users",
    ]
    for table in tables:
        op.alter_column(
            table,
            "tenant_id",
            existing_type=sa.UUID(),
            nullable=True,
            server_default=None,
        )
