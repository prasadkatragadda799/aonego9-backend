"""vendor gallery and portfolio multi-image

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vendors",
        sa.Column("gallery_urls_json", sa.Text(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "portfolio_items",
        sa.Column("images_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("portfolio_items", "images_json")
    op.drop_column("vendors", "gallery_urls_json")
