"""Seed subscription plans and an admin user so the apps work out of the box."""
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.subscription import SubscriptionPlan
from app.models.user import User, ApprovalStatus
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

        # Admin user
        admin_email = "admin@aonego9.com"
        existing_admin = (await db.execute(select(User).where(User.email == admin_email))).scalar_one_or_none()
        if not existing_admin:
            admin = User(
                name="Super Admin",
                email=admin_email,
                password_hash=hash_password("demo1234"),
                is_admin=True,
                status=ApprovalStatus.approved,
                verified=True,
            )
            db.add(admin)

        await db.commit()
        print("✓ Seeded: subscription plans + admin user (admin@aonego9.com / demo1234)")

asyncio.run(seed())
