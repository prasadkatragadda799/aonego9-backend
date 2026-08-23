"""newsletter, advance requests, otp, admin city

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "newsletter_issues",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tag", sa.String(length=80), nullable=False, server_default="Digest"),
        sa.Column("city", sa.String(length=100), nullable=False, server_default="India"),
        sa.Column("emoji", sa.String(length=10), nullable=False, server_default="✦"),
        sa.Column("bg", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("author", sa.String(length=120), nullable=False, server_default="AOneGo9 Desk"),
        sa.Column("author_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("organisation", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("credentials_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "newsletter_contributions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("city", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("organisation", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("headline", sa.String(length=300), nullable=False),
        sa.Column("story", sa.Text(), nullable=False, server_default=""),
        sa.Column("credentials_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "advance_payment_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("booking_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="5000"),
        sa.Column("receipt_image", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_advance_payment_requests_booking_id", "advance_payment_requests", ["booking_id"])
    op.create_index("ix_advance_payment_requests_user_id", "advance_payment_requests", ["user_id"])
    op.create_table(
        "phone_otps",
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("phone", "purpose"),
    )
    op.add_column("users", sa.Column("admin_city", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("vendors", sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("vendors", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("vendors", sa.Column("categories_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("vendors", "categories_json")
    op.drop_column("vendors", "last_login_at")
    op.drop_column("vendors", "phone_verified")
    op.drop_column("users", "admin_city")
    op.drop_table("phone_otps")
    op.drop_index("ix_advance_payment_requests_user_id", "advance_payment_requests")
    op.drop_index("ix_advance_payment_requests_booking_id", "advance_payment_requests")
    op.drop_table("advance_payment_requests")
    op.drop_table("newsletter_contributions")
    op.drop_table("newsletter_issues")
