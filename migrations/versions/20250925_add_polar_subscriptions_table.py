"""add polar subscriptions table

Revision ID: b60e49215224
Revises: merge_heads_20250920
Create Date: 2025-08-10 11:14:14.603240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b60e49215224'
down_revision = 'merge_heads_20250920'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'polar_subscriptions',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('polar_subscription_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('tier', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('polar_subscription_id'),
    )
    op.create_index(
        op.f('ix_polar_subscriptions_user_id'),
        'polar_subscriptions',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_polar_subscriptions_polar_subscription_id'),
        'polar_subscriptions',
        ['polar_subscription_id'],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f('ix_polar_subscriptions_polar_subscription_id'),
        table_name='polar_subscriptions',
    )
    op.drop_index(
        op.f('ix_polar_subscriptions_user_id'),
        table_name='polar_subscriptions',
    )
    op.drop_table('polar_subscriptions')
