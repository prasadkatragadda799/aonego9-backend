import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_any_authenticated, get_current_admin
from app.models.subscription import (
    BillingEntry,
    ClientSubscription,
    PaymentSettings,
    SubscriptionPlan,
    SubscriptionRequest,
    VendorSubscription,
)
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.subscription import (
    BillingEntryOut,
    ClientSubscriptionOut,
    PaymentSettingsIn,
    PaymentSettingsOut,
    PlanCreateUpdate,
    SubscriptionPlanOut,
    SubscriptionRequestIn,
    SubscriptionRequestOut,
    SubscriptionReviewIn,
    VendorSubscriptionOut,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


async def _party_from_payload(payload: dict, db: AsyncSession) -> tuple[str, Vendor | User]:
    """Resolves the caller's JWT payload to ("vendor"|"user", the row), or 403s."""
    role = payload.get("role")
    if role == "vendor":
        result = await db.execute(select(Vendor).where(Vendor.id == payload["sub"]))
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(status_code=401, detail="Vendor not found")
        return "vendor", vendor
    if role == "user":
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return "user", user
    raise HTTPException(status_code=403, detail="Vendor or user access only")


# ── Public ────────────────────────────────────────────────────────


@router.get("/plans", response_model=list[SubscriptionPlanOut])
async def list_plans(audience: str | None = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan))
    plans = result.scalars().all()
    if audience:
        plans = [p for p in plans if p.audience in (audience, "both")]
    return [SubscriptionPlanOut.from_orm(p) for p in plans]


@router.get("/payment-info", response_model=PaymentSettingsOut)
async def payment_info(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentSettings).where(PaymentSettings.id == "default"))
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        return PaymentSettingsOut(upi_id="", payee_name="AOneGo9")
    return settings_row


# ── Vendor / user (self) ─────────────────────────────────────────


@router.get("/me")
async def get_my_subscription(
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    kind, party = await _party_from_payload(payload, db)
    if kind == "vendor":
        result = await db.execute(select(VendorSubscription).where(VendorSubscription.vendor_id == party.id))
        sub = result.scalar_one_or_none()
        if not sub:
            raise HTTPException(status_code=404, detail="No active subscription found")
        return VendorSubscriptionOut.model_validate(sub)
    result = await db.execute(select(ClientSubscription).where(ClientSubscription.user_id == party.id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return ClientSubscriptionOut.model_validate(sub)


@router.post("/request", response_model=SubscriptionRequestOut)
async def request_subscription(
    body: SubscriptionRequestIn,
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    kind, party = await _party_from_payload(payload, db)
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == body.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    req = SubscriptionRequest(
        requester_type=kind,
        vendor_id=party.id if kind == "vendor" else None,
        user_id=party.id if kind == "user" else None,
        plan_id=plan.id,
        plan_name=plan.name,
        amount=plan.price,
        receipt_image=body.receipt_image,
        status="pending",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/requests/mine", response_model=list[SubscriptionRequestOut])
async def my_requests(
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    kind, party = await _party_from_payload(payload, db)
    field = SubscriptionRequest.vendor_id if kind == "vendor" else SubscriptionRequest.user_id
    result = await db.execute(
        select(SubscriptionRequest).where(field == party.id).order_by(SubscriptionRequest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/billing", response_model=list[BillingEntryOut])
async def list_billing(
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    kind, party = await _party_from_payload(payload, db)
    if kind != "vendor":
        return []
    result = await db.execute(
        select(BillingEntry).where(BillingEntry.vendor_id == party.id).order_by(BillingEntry.date.desc())
    )
    return result.scalars().all()


# ── Admin ─────────────────────────────────────────────────────────


@router.get("/admin/plans", response_model=list[SubscriptionPlanOut], dependencies=[Depends(get_current_admin)])
async def admin_list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan))
    return [SubscriptionPlanOut.from_orm(p) for p in result.scalars().all()]


@router.post("/admin/plans", response_model=SubscriptionPlanOut, dependencies=[Depends(get_current_admin)])
async def admin_create_plan(body: PlanCreateUpdate, db: AsyncSession = Depends(get_db)):
    plan = SubscriptionPlan(
        id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        name=body.name,
        price=body.price,
        period=body.period,
        features="\n".join(body.features),
        recommended=body.recommended,
        audience=body.audience,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return SubscriptionPlanOut.from_orm(plan)


@router.put("/admin/plans/{plan_id}", response_model=SubscriptionPlanOut, dependencies=[Depends(get_current_admin)])
async def admin_update_plan(plan_id: str, body: PlanCreateUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.name = body.name
    plan.price = body.price
    plan.period = body.period
    plan.features = "\n".join(body.features)
    plan.recommended = body.recommended
    plan.audience = body.audience
    await db.commit()
    await db.refresh(plan)
    return SubscriptionPlanOut.from_orm(plan)


@router.delete("/admin/plans/{plan_id}", dependencies=[Depends(get_current_admin)])
async def admin_delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(plan)
    await db.commit()
    return {"ok": True}


@router.get("/admin/payment-info", response_model=PaymentSettingsOut, dependencies=[Depends(get_current_admin)])
async def admin_get_payment_info(db: AsyncSession = Depends(get_db)):
    return await payment_info(db)


@router.put("/admin/payment-info", response_model=PaymentSettingsOut, dependencies=[Depends(get_current_admin)])
async def admin_set_payment_info(body: PaymentSettingsIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentSettings).where(PaymentSettings.id == "default"))
    row = result.scalar_one_or_none()
    if not row:
        row = PaymentSettings(id="default")
        db.add(row)
    row.upi_id = body.upi_id
    row.payee_name = body.payee_name
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/admin/requests",
    response_model=list[SubscriptionRequestOut],
    dependencies=[Depends(get_current_admin)],
)
async def admin_list_requests(status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(SubscriptionRequest)
    if status:
        q = q.where(SubscriptionRequest.status == status)
    result = await db.execute(q.order_by(SubscriptionRequest.created_at.desc()))
    return result.scalars().all()


@router.post(
    "/admin/requests/{request_id}/approve",
    response_model=SubscriptionRequestOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_approve_request(request_id: str, body: SubscriptionReviewIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionRequest).where(SubscriptionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already reviewed")

    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == req.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    renews_on = datetime.now(timezone.utc) + timedelta(days=30)

    if req.requester_type == "vendor":
        sub_result = await db.execute(select(VendorSubscription).where(VendorSubscription.vendor_id == req.vendor_id))
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.plan_id = plan.id
            sub.plan_name = plan.name
            sub.price = plan.price
            sub.status = "active"
            sub.renews_on = renews_on
        else:
            sub = VendorSubscription(
                vendor_id=req.vendor_id,
                plan_id=plan.id,
                plan_name=plan.name,
                price=plan.price,
                status="active",
                renews_on=renews_on,
            )
            db.add(sub)
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == req.vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        if vendor:
            vendor.plan = plan.name
        if plan.price > 0:
            db.add(BillingEntry(
                vendor_id=req.vendor_id,
                description=f"{plan.name} plan — {datetime.now(timezone.utc).strftime('%B %Y')}",
                amount=plan.price,
                status="paid",
            ))
    else:
        sub_result = await db.execute(select(ClientSubscription).where(ClientSubscription.user_id == req.user_id))
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.plan_id = plan.id
            sub.plan_name = plan.name
            sub.price = plan.price
            sub.status = "active"
            sub.renews_on = renews_on
        else:
            sub = ClientSubscription(
                user_id=req.user_id,
                plan_id=plan.id,
                plan_name=plan.name,
                price=plan.price,
                status="active",
                renews_on=renews_on,
            )
            db.add(sub)

    req.status = "approved"
    req.admin_note = body.admin_note
    req.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(req)
    return req


@router.post(
    "/admin/requests/{request_id}/reject",
    response_model=SubscriptionRequestOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_reject_request(request_id: str, body: SubscriptionReviewIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionRequest).where(SubscriptionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already reviewed")
    req.status = "rejected"
    req.admin_note = body.admin_note
    req.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(req)
    return req
