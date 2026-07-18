"""Idempotent startup bootstrapping — safe to call on every boot.

Ensures the fixed superadmin account exists so a fresh deploy (empty
database) always has a working admin login without needing shell access
to run seed.py by hand.
"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import ApprovalStatus, User


async def ensure_admin_exists(db: AsyncSession) -> None:
    existing = (await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))).scalar_one_or_none()
    if existing:
        if not existing.is_admin:
            existing.is_admin = True
            await db.commit()
        return
    admin = User(
        name="Super Admin",
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        is_admin=True,
        status=ApprovalStatus.approved,
        verified=True,
    )
    db.add(admin)
    try:
        await db.commit()
    except IntegrityError:
        # Gunicorn boots multiple worker processes, each running this same
        # startup hook concurrently — the first to commit wins the insert,
        # every other worker hits the unique constraint on email. That's
        # fine, it just means the account already exists; nothing to do.
        await db.rollback()
