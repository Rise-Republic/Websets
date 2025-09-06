"""Add verification token columns"""

from alembic import op
import sqlalchemy as sa

revision = "add_verification_fields_20250906"
down_revision = "add_tenant_fields_20250905"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("verification_token", sa.String(), nullable=True))
    op.add_column(
        "users", sa.Column("verification_token_expiry", sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column("users", "verification_token_expiry")
    op.drop_column("users", "verification_token")
