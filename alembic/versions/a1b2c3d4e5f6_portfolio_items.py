"""portfolio items

Revision ID: a1b2c3d4e5f6
Revises: 5be4e53950a3
Create Date: 2026-08-13 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5be4e53950a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'portfolio_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('headline', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tag', sa.String(length=80), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('bg', sa.Integer(), nullable=False),
        sa.Column('featured', sa.Boolean(), nullable=False),
        sa.Column('type', sa.String(length=40), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('portfolio_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_portfolio_items_vendor_id'), ['vendor_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('portfolio_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_portfolio_items_vendor_id'))
    op.drop_table('portfolio_items')
