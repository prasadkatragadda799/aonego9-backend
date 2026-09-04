"""directory desks (ads, sessions, partners, team, social, leads) and vendor
profile brand work / awards / projects / socials / dob / hair length

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ad_creatives',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('media', sa.String(length=10), nullable=False),
        sa.Column('headline', sa.String(length=300), nullable=False),
        sa.Column('sub', sa.String(length=500), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('profile_name', sa.String(length=200), nullable=False),
        sa.Column('profile_cat', sa.String(length=80), nullable=False),
        sa.Column('website_url', sa.String(length=500), nullable=False),
        sa.Column('label', sa.String(length=80), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False),
        sa.Column('clicks', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('mode', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('host', sa.String(length=200), nullable=False),
        sa.Column('division', sa.String(length=40), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('date', sa.String(length=40), nullable=False),
        sa.Column('time', sa.String(length=40), nullable=False),
        sa.Column('duration', sa.String(length=40), nullable=False),
        sa.Column('fee', sa.String(length=40), nullable=False),
        sa.Column('seats', sa.Integer(), nullable=False),
        sa.Column('seats_left', sa.Integer(), nullable=False),
        sa.Column('blurb', sa.Text(), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('registrations', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'logo_partners',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('tagline', sa.String(length=500), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('division', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'team_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=200), nullable=False),
        sa.Column('desk', sa.String(length=100), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'social_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(length=40), nullable=False),
        sa.Column('handle', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('followers', sa.Integer(), nullable=False),
        sa.Column('connected', sa.Boolean(), nullable=False),
        sa.Column('owner', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'leads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('vendor_profile_details') as batch_op:
        batch_op.add_column(sa.Column('dob', sa.String(length=20), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('hair_length', sa.String(length=40), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('awards_json', sa.Text(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('brand_work_json', sa.Text(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('projects_json', sa.Text(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('socials_json', sa.Text(), nullable=False, server_default='[]'))


def downgrade() -> None:
    with op.batch_alter_table('vendor_profile_details') as batch_op:
        batch_op.drop_column('socials_json')
        batch_op.drop_column('projects_json')
        batch_op.drop_column('brand_work_json')
        batch_op.drop_column('awards_json')
        batch_op.drop_column('hair_length')
        batch_op.drop_column('dob')

    op.drop_table('leads')
    op.drop_table('social_accounts')
    op.drop_table('team_members')
    op.drop_table('logo_partners')
    op.drop_table('sessions')
    op.drop_table('ad_creatives')
