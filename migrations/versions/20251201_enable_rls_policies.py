"""Enable RLS on tenant tables

Revision ID: c0a1b2c3d4e5
Revises: b60e49215224
Create Date: 2025-12-01
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c0a1b2c3d4e5"
down_revision = "b60e49215224"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE datasets ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON datasets
        USING (tenant_id::text = current_setting('app.current_tenant'))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant'))
        """
    )
    op.execute("ALTER TABLE datasets FORCE ROW LEVEL SECURITY")

    op.execute("ALTER TABLE data_records ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON data_records
        USING (tenant_id::text = current_setting('app.current_tenant'))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant'))
        """
    )
    op.execute("ALTER TABLE data_records FORCE ROW LEVEL SECURITY")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON data_records")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON datasets")
    op.execute("ALTER TABLE data_records DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE datasets DISABLE ROW LEVEL SECURITY")
