"""payment_settings.advance_amount

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-10-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payment_settings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("advance_amount", sa.Float(), server_default="5000", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("payment_settings", schema=None) as batch_op:
        batch_op.drop_column("advance_amount")
