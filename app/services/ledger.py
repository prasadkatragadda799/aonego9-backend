"""The money ledger: every rupee that moves is recorded once.

Before this, ledger rows were only written when an admin recorded a payout,
so vendor Earnings and the admin Payments page could never reflect actual
bookings, advances, commission or subscriptions.

  advance approved   -> PaymentTxn(advance, paid)
  booking completed  -> PaymentTxn(booking, paid)      gross
                        PaymentTxn(commission, paid)   platform share
                        EarningTxn(earning)            vendor net — "pending"
                                                       until the payout hold
                                                       passes, then "settled"
  booking cancelled  -> PaymentTxn(refund, pending) for any advance taken
  subscription paid  -> PaymentTxn(subscription, paid)

Each write is idempotent per booking / request, so a status that is set
twice never double-counts.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.payment import EarningTxn, PaymentStatus, PaymentTxn, TxnType
from app.services.platform_settings import load_platform_settings


async def _exists(db: AsyncSession, booking_id: str, txn_type: TxnType) -> bool:
    row = await db.execute(
        select(PaymentTxn.id).where(PaymentTxn.booking_id == booking_id, PaymentTxn.type == txn_type).limit(1)
    )
    return row.scalar_one_or_none() is not None


async def record_advance(db: AsyncSession, booking: Booking, amount: float, client_name: str) -> None:
    db.add(PaymentTxn(
        booking_id=booking.id,
        party=client_name or "Client",
        type=TxnType.advance,
        amount=amount,
        status=PaymentStatus.paid,
        method="UPI",
    ))


async def record_completion(db: AsyncSession, booking: Booking, client_name: str) -> None:
    if booking.amount <= 0 or await _exists(db, booking.id, TxnType.booking):
        return
    settings = await load_platform_settings(db)
    rate = max(0.0, min(50.0, float(settings.get("commission_percent", 15)))) / 100.0
    commission = round(booking.amount * rate, 2)
    hold_hours = int(settings.get("payout_hold_hours", 48) or 0)
    db.add(PaymentTxn(booking_id=booking.id, party=client_name or "Client", type=TxnType.booking,
                      amount=booking.amount, status=PaymentStatus.paid, method="Booking"))
    if commission > 0:
        db.add(PaymentTxn(booking_id=booking.id, party="AOneGo9", type=TxnType.commission,
                          amount=commission, status=PaymentStatus.paid, method=f"{rate * 100:.0f}%"))
    db.add(EarningTxn(
        vendor_id=booking.vendor_id,
        booking_id=booking.id,
        source=f"{booking.service} · {client_name or 'Client'}"[:200],
        type=TxnType.earning,
        amount=round(booking.amount - commission, 2),
        status="pending" if hold_hours > 0 else "settled",
    ))


async def record_refund(db: AsyncSession, booking: Booking, client_name: str) -> None:
    if booking.advance_paid <= 0 or await _exists(db, booking.id, TxnType.refund):
        return
    db.add(PaymentTxn(booking_id=booking.id, party=client_name or "Client", type=TxnType.refund,
                      amount=booking.advance_paid, status=PaymentStatus.pending, method="UPI"))


async def record_subscription(db: AsyncSession, party: str, amount: float, plan_name: str) -> None:
    if amount <= 0:
        return
    db.add(PaymentTxn(party=party or "Subscriber", type=TxnType.subscription, amount=amount,
                      status=PaymentStatus.paid, method=f"UPI · {plan_name}"[:50]))


async def settle_due_earnings(db: AsyncSession, vendor_id: str | None = None) -> None:
    """Move net earnings from pending to settled once the payout hold passes."""
    settings = await load_platform_settings(db)
    hold = timedelta(hours=int(settings.get("payout_hold_hours", 48) or 0))
    cutoff = datetime.now(timezone.utc) - hold
    q = update(EarningTxn).where(
        EarningTxn.type == TxnType.earning,
        EarningTxn.status == "pending",
        EarningTxn.date <= cutoff,
    )
    if vendor_id:
        q = q.where(EarningTxn.vendor_id == vendor_id)
    await db.execute(q.values(status="settled"))
    await db.commit()
