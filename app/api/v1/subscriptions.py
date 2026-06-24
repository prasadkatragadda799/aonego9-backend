from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_vendor
from app.models.subscription import BillingEntry, SubscriptionPlan, VendorSubscription
from app.models.vendor import Vendor
from app.schemas.subscription import (
    BillingEntryOut,
    SubscribeRequest,
    SubscriptionPlanOut,
    VendorSubscriptionOut,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan))
    plans = result.scalars().all()
    return [SubscriptionPlanOut.from_orm(p) for p in plans]


@router.get("/me", response_model=VendorSubscriptionOut)
async def get_my_subscription(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VendorSubscription).where(VendorSubscription.vendor_id == vendor.id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub


@router.post("/subscribe", response_model=VendorSubscriptionOut)
async def subscribe(
    body: SubscribeRequest,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == body.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    sub_result = await db.execute(select(VendorSubscription).where(VendorSubscription.vendor_id == vendor.id))
    sub = sub_result.scalar_one_or_none()

    renews_on = datetime.now(timezone.utc) + timedelta(days=30)
    if sub:
        sub.plan_id = plan.id
        sub.plan_name = plan.name
        sub.price = plan.price
        sub.status = "active"
        sub.renews_on = renews_on
    else:
        sub = VendorSubscription(
            vendor_id=vendor.id,
            plan_id=plan.id,
            plan_name=plan.name,
            price=plan.price,
            status="active",
            renews_on=renews_on,
        )
        db.add(sub)

    # Update vendor plan label
    vendor.plan = plan.name

    # Record billing entry
    if plan.price > 0:
        entry = BillingEntry(
            vendor_id=vendor.id,
            description=f"{plan.name} plan — {datetime.now(timezone.utc).strftime('%B %Y')}",
            amount=plan.price,
            status="paid",
        )
        db.add(entry)

    await db.commit()
    await db.refresh(sub)
    return sub


@router.get("/billing", response_model=list[BillingEntryOut])
async def list_billing(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BillingEntry)
        .where(BillingEntry.vendor_id == vendor.id)
        .order_by(BillingEntry.date.desc())
    )
    return result.scalars().all()
