"""vendor profile details

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vendor_profile_details',
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('experience', sa.String(length=80), nullable=False),
        sa.Column('training', sa.String(length=200), nullable=False),
        sa.Column('languages', sa.String(length=200), nullable=False),
        sa.Column('overview', sa.Text(), nullable=False),
        sa.Column('height', sa.String(length=20), nullable=False),
        sa.Column('weight', sa.String(length=20), nullable=False),
        sa.Column('bust', sa.String(length=20), nullable=False),
        sa.Column('chest', sa.String(length=20), nullable=False),
        sa.Column('waist', sa.String(length=20), nullable=False),
        sa.Column('hip', sa.String(length=20), nullable=False),
        sa.Column('shoe', sa.String(length=20), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('hair', sa.String(length=40), nullable=False),
        sa.Column('eye', sa.String(length=40), nullable=False),
        sa.Column('skin', sa.String(length=40), nullable=False),
        sa.Column('stats_json', sa.Text(), nullable=False),
        sa.Column('tags_json', sa.Text(), nullable=False),
        sa.Column('services_json', sa.Text(), nullable=False),
        sa.Column('amenities_json', sa.Text(), nullable=False),
        sa.Column('availability_json', sa.Text(), nullable=False),
        sa.Column('scene_data_json', sa.Text(), nullable=False),
        sa.Column('spaces_json', sa.Text(), nullable=False),
        sa.Column('equipment_json', sa.Text(), nullable=False),
        sa.Column('reels_json', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.PrimaryKeyConstraint('vendor_id'),
    )


def downgrade() -> None:
    op.drop_table('vendor_profile_details')
