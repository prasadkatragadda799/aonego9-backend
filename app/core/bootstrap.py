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
from app.models.subscription import PaymentSettings, SubscriptionPlan
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


DEFAULT_PLANS = [
    dict(id="PLAN-FREE", name="Starter", price=0.0, period="forever",
         features=["Limited listings", "Basic support"], recommended=False, audience="both"),
    dict(id="PLAN-PRO", name="Pro", price=999.0, period="per month",
         features=["Unlimited listings", "Priority support", "Featured placement"], recommended=True, audience="both"),
    dict(id="PLAN-PREMIUM", name="Premium", price=2499.0, period="per month",
         features=["Everything in Pro", "Dedicated account manager", "Advanced analytics"], recommended=False, audience="both"),
]


async def ensure_subscription_defaults(db: AsyncSession) -> None:
    existing = (await db.execute(select(SubscriptionPlan))).scalars().first()
    if not existing:
        for p in DEFAULT_PLANS:
            db.add(SubscriptionPlan(
                id=p["id"], name=p["name"], price=p["price"], period=p["period"],
                features="\n".join(p["features"]), recommended=p["recommended"], audience=p["audience"],
            ))
    settings_row = (await db.execute(select(PaymentSettings).where(PaymentSettings.id == "default"))).scalar_one_or_none()
    if not settings_row:
        db.add(PaymentSettings(id="default", upi_id="", payee_name="AOneGo9"))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
