"""event venue / description / image, and platform settings

Revision ID: g7b8c9d0e1f2
Revises: a7b8c9d0e1f2
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('platform_events') as batch:
        batch.add_column(sa.Column('venue', sa.String(length=200), nullable=False, server_default=''))
        batch.add_column(sa.Column('description', sa.Text(), nullable=False, server_default=''))
        batch.add_column(sa.Column('image_url', sa.String(length=500), nullable=False, server_default=''))
    op.create_table(
        'platform_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value_json', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    op.drop_table('platform_settings')
    with op.batch_alter_table('platform_events') as batch:
        batch.drop_column('image_url')
        batch.drop_column('description')
        batch.drop_column('venue')
