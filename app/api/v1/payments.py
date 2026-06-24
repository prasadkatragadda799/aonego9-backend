from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_vendor
from app.models.payment import EarningTxn, PaymentStatus, PaymentTxn, TxnType
from app.models.vendor import Vendor
from app.schemas.payment import (
    EarningsListOut,
    EarningTxnOut,
    PaymentListOut,
    PaymentTxnOut,
    PayoutRequest,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/admin", response_model=PaymentListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(PaymentTxn)
    if type:
        q = q.where(PaymentTxn.type == TxnType(type))
    if status:
        q = q.where(PaymentTxn.status == PaymentStatus(status))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.order_by(PaymentTxn.date.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [PaymentTxnOut.model_validate(t) for t in result.scalars().all()]
    return PaymentListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/earnings", response_model=EarningsListOut)
async def list_earnings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    q = select(EarningTxn).where(EarningTxn.vendor_id == vendor.id)
    all_result = await db.execute(q)
    all_txns = all_result.scalars().all()

    total_earned = sum(t.amount for t in all_txns if t.type == TxnType.earning)
    total_pending = sum(t.amount for t in all_txns if t.type == TxnType.earning and t.status == "pending")
    total_paid_out = sum(t.amount for t in all_txns if t.type == TxnType.payout)

    paginated = await db.execute(q.order_by(EarningTxn.date.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [EarningTxnOut.model_validate(t) for t in paginated.scalars().all()]
    return EarningsListOut(
        items=items,
        total_earned=total_earned,
        total_pending=total_pending,
        total_paid_out=total_paid_out,
        page=page,
        page_size=page_size,
    )


@router.post("/payout", dependencies=[Depends(get_current_admin)])
async def trigger_payout(body: PayoutRequest, db: AsyncSession = Depends(get_db)):
    txn = PaymentTxn(
        party=body.vendor_id,
        type=TxnType.payout,
        amount=body.amount,
        status=PaymentStatus.payout,
        method=body.method,
    )
    db.add(txn)
    earning = EarningTxn(
        vendor_id=body.vendor_id,
        source=f"Payout — {body.method}",
        type=TxnType.payout,
        amount=body.amount,
        status="settled",
    )
    db.add(earning)
    await db.commit()
    return {"message": "Payout triggered", "amount": body.amount}
