"""Add encrypted_blob column"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_encrypted_blob_20250810'
down_revision = 'add_indexes_20250801'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('data_records', sa.Column('encrypted_blob', sa.LargeBinary(), nullable=True))

def downgrade():
    op.drop_column('data_records', 'encrypted_blob')
