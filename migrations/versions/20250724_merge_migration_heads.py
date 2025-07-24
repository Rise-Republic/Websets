"""Merge migration heads

Revision ID: merge_heads_20250724
Revises: add_encrypted_blob_20250810, make_tenant_id_non_nullable_20250915
Create Date: 2025-07-24 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads_20250724'
down_revision = ('add_encrypted_blob_20250810', 'tenant_id_non_null_20250915')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no actual schema changes needed
    pass


def downgrade():
    # This is a merge migration - no actual schema changes needed
    pass
