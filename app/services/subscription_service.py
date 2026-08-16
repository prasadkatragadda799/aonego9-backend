"""Shared helpers for activating and assigning subscriptions."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import (
    BillingEntry,
    ClientSubscription,
    SubscriptionPlan,
    VendorSubscription,
)
from app.models.vendor import Vendor


def _renewal_date(plan: SubscriptionPlan) -> datetime:
    now = datetime.now(timezone.utc)
    period = (plan.period or "").lower()
    if "year" in period:
        return now + timedelta(days=365)
    if plan.price == 0 or "forever" in period:
        return now + timedelta(days=3650)
    return now + timedelta(days=30)


async def activate_vendor_subscription(
    db: AsyncSession,
    *,
    vendor_id: str,
    plan: SubscriptionPlan,
    create_billing: bool = True,
) -> VendorSubscription:
    renews_on = _renewal_date(plan)
    sub_result = await db.execute(select(VendorSubscription).where(VendorSubscription.vendor_id == vendor_id))
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.plan_id = plan.id
        sub.plan_name = plan.name
        sub.price = plan.price
        sub.status = "active"
        sub.renews_on = renews_on
    else:
        sub = VendorSubscription(
            vendor_id=vendor_id,
            plan_id=plan.id,
            plan_name=plan.name,
            price=plan.price,
            status="active",
            renews_on=renews_on,
        )
        db.add(sub)

    vendor_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = vendor_result.scalar_one_or_none()
    if vendor:
        vendor.plan = plan.name

    if create_billing and plan.price > 0:
        db.add(
            BillingEntry(
                vendor_id=vendor_id,
                description=f"{plan.name} plan — {datetime.now(timezone.utc).strftime('%B %Y')}",
                amount=plan.price,
                status="paid",
            )
        )
    return sub


async def activate_client_subscription(
    db: AsyncSession,
    *,
    user_id: str,
    plan: SubscriptionPlan,
) -> ClientSubscription:
    renews_on = _renewal_date(plan)
    sub_result = await db.execute(select(ClientSubscription).where(ClientSubscription.user_id == user_id))
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.plan_id = plan.id
        sub.plan_name = plan.name
        sub.price = plan.price
        sub.status = "active"
        sub.renews_on = renews_on
    else:
        sub = ClientSubscription(
            user_id=user_id,
            plan_id=plan.id,
            plan_name=plan.name,
            price=plan.price,
            status="active",
            renews_on=renews_on,
        )
        db.add(sub)
    return sub


async def default_vendor_plan(db: AsyncSession) -> SubscriptionPlan | None:
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.audience.in_(("vendor", "both")))
        .order_by(SubscriptionPlan.price, SubscriptionPlan.name)
    )
    return result.scalars().first()
