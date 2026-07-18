"""Seed subscription plans and an admin user so the apps work out of the box.

The admin account itself is also auto-provisioned on every backend startup
(see app.core.bootstrap.ensure_admin_exists) — this script exists for local
dev convenience and for seeding the subscription plans, which startup
bootstrapping intentionally doesn't touch.
"""
import asyncio
from app.core.bootstrap import ensure_admin_exists
from app.core.database import AsyncSessionLocal
from app.models.subscription import SubscriptionPlan
from sqlalchemy import select

PLANS = [
    SubscriptionPlan(id="starter", name="Starter", price=0, period="forever", recommended=False,
        features="Public profile & portfolio\nUp to 3 service packages\nReceive inquiries\n10% platform commission"),
    SubscriptionPlan(id="pro", name="Pro", price=999, period="per month", recommended=True,
        features="Everything in Starter\nUnlimited packages & roster\nPriority in search results\nFeatured on category page\n7% platform commission\nCalendar & messaging"),
    SubscriptionPlan(id="elite", name="Elite", price=2999, period="per month", recommended=False,
        features="Everything in Pro\nTop placement + live poster eligibility\nVerified Elite badge\nDedicated account manager\n5% platform commission\nAdvanced analytics"),
]

async def seed():
    async with AsyncSessionLocal() as db:
        # Plans
        for plan in PLANS:
            existing = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan.id))).scalar_one_or_none()
            if not existing:
                db.add(plan)
        await db.commit()

        # Admin user — same fixed-credential bootstrap the backend runs on every startup.
        await ensure_admin_exists(db)
        print("✓ Seeded: subscription plans + admin user")

asyncio.run(seed())
