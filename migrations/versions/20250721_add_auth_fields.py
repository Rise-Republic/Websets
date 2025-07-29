"""
Alembic migration script for new authentication fields:
- mfa_method
- password_reset_token
- password_reset_expiry
- refresh_token
- refresh_token_expiry
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_auth_fields_20250721'
down_revision = 'initial_schema_sqlite'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('mfa_method', sa.String(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('password_reset_expiry', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('refresh_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('refresh_token_expiry', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('users', 'mfa_method')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'password_reset_expiry')
    op.drop_column('users', 'refresh_token')
    op.drop_column('users', 'refresh_token_expiry')
