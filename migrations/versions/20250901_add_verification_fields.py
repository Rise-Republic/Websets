"""Add email verification columns"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_verification_fields_20250901"
down_revision = "add_indexes_20250801"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("verification_token", sa.String(), nullable=True))
    op.add_column(
        "users", sa.Column("verification_token_expiry", sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column("users", "verification_token")
    op.drop_column("users", "verification_token_expiry")
