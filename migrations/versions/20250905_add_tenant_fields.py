"""Add tenant_id columns for multi-tenancy"""

from alembic import op
import sqlalchemy as sa

revision = "add_tenant_fields_20250905"
down_revision = "add_indexes_20250801"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("datasets", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("data_records", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("discovered_urls", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("crawl_results", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("data_access_logs", sa.Column("tenant_id", sa.UUID(), nullable=True))


def downgrade():
    op.drop_column("data_access_logs", "tenant_id")
    op.drop_column("crawl_results", "tenant_id")
    op.drop_column("discovered_urls", "tenant_id")
    op.drop_column("data_records", "tenant_id")
    op.drop_column("datasets", "tenant_id")
    op.drop_column("jobs", "tenant_id")
