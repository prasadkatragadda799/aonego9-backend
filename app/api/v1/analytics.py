from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_vendor
from app.models.booking import Booking, BookingStatus
from app.models.notification import Notification
from app.models.payment import EarningTxn, PaymentTxn, TxnType
from app.models.review import Review
from app.models.user import ApprovalStatus, User
from app.models.vendor import Vendor
from app.schemas.analytics import CategoryShare, DashboardKpis, KpiPoint, TrendData, VendorDashboardKpis

router = APIRouter(prefix="/analytics", tags=["analytics"])

_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _last_n_months(n: int) -> list[tuple[int, int]]:
    """Return (year, month) tuples for the last n months, oldest first."""
    now = datetime.now(timezone.utc)
    months = []
    year, month = now.year, now.month
    for _ in range(n):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


def _bucket_by_month(rows: list[tuple[datetime, float]], months: list[tuple[int, int]]) -> list[KpiPoint]:
    totals: dict[tuple[int, int], float] = {ym: 0.0 for ym in months}
    for dt, value in rows:
        key = (dt.year, dt.month)
        if key in totals:
            totals[key] += value
    return [KpiPoint(label=_MONTH_LABELS[m - 1], value=totals[(y, m)]) for y, m in months]


@router.get("/admin/dashboard", response_model=DashboardKpis, dependencies=[Depends(get_current_admin)])
async def admin_dashboard(db: AsyncSession = Depends(get_db)):
    total_vendors = (await db.execute(select(func.count(Vendor.id)))).scalar_one()
    pending_approvals = (
        await db.execute(select(func.count(Vendor.id)).where(Vendor.status == ApprovalStatus.pending))
    ).scalar_one()
    total_users = (await db.execute(select(func.count(User.id)).where(User.is_admin == False))).scalar_one()
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar_one()
    active_bookings = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.status.in_([BookingStatus.confirmed, BookingStatus.in_progress])
            )
        )
    ).scalar_one()
    total_revenue = (
        await db.execute(
            select(func.coalesce(func.sum(PaymentTxn.amount), 0)).where(PaymentTxn.type == TxnType.booking)
        )
    ).scalar_one()
    commission = total_revenue * 0.08  # platform's ~8% blended commission
    disputes = (
        await db.execute(select(func.count(Booking.id)).where(Booking.status == BookingStatus.disputed))
    ).scalar_one()

    return DashboardKpis(
        total_vendors=total_vendors,
        pending_approvals=pending_approvals,
        total_users=total_users,
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        disputes=disputes,
        total_revenue=float(total_revenue),
        monthly_revenue=float(total_revenue) / 6,
        commission_earned=commission,
    )


@router.get("/admin/trends", dependencies=[Depends(get_current_admin)])
async def admin_trends(db: AsyncSession = Depends(get_db)) -> dict:
    months = _last_n_months(6)
    start = datetime(months[0][0], months[0][1], 1, tzinfo=timezone.utc)

    revenue_rows = (
        await db.execute(
            select(PaymentTxn.date, PaymentTxn.amount).where(
                PaymentTxn.type == TxnType.booking, PaymentTxn.date >= start
            )
        )
    ).all()
    revenue_points = _bucket_by_month([(r.date, r.amount) for r in revenue_rows], months)

    signup_rows = (
        await db.execute(select(User.joined_at).where(User.is_admin == False, User.joined_at >= start))
    ).all()
    signup_points = _bucket_by_month([(r.joined_at, 1.0) for r in signup_rows], months)

    category_rows = (
        await db.execute(select(Vendor.category, func.count(Vendor.id)).group_by(Vendor.category))
    ).all()
    category_share = [KpiPoint(label=cat or "Other", value=float(count)) for cat, count in category_rows]

    return {
        "revenue": TrendData(points=revenue_points),
        "signups": TrendData(points=signup_points),
        "category_share": CategoryShare(shares=category_share),
    }


@router.get("/vendor/dashboard", response_model=VendorDashboardKpis)
async def vendor_dashboard(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    bookings_q = select(Booking).where(Booking.vendor_id == vendor.id)
    all_bookings = (await db.execute(bookings_q)).scalars().all()

    total = len(all_bookings)
    active = sum(1 for b in all_bookings if b.status in [BookingStatus.confirmed, BookingStatus.in_progress])
    pending = sum(1 for b in all_bookings if b.status == BookingStatus.requested)
    completed = sum(1 for b in all_bookings if b.status == BookingStatus.completed)

    earnings_q = select(EarningTxn).where(EarningTxn.vendor_id == vendor.id)
    all_txns = (await db.execute(earnings_q)).scalars().all()
    total_earned = sum(t.amount for t in all_txns if t.type == TxnType.earning)
    pending_payout = sum(t.amount for t in all_txns if t.type == TxnType.earning and t.status == "pending")

    reviews = (await db.execute(select(Review).where(Review.vendor_id == vendor.id))).scalars().all()
    avg_rating = sum(r.stars for r in reviews) / len(reviews) if reviews else 0.0

    unread = (
        await db.execute(
            select(func.count(Notification.id)).where(
                Notification.vendor_id == vendor.id, Notification.unread == True
            )
        )
    ).scalar_one()

    return VendorDashboardKpis(
        total_bookings=total,
        active_bookings=active,
        pending_requests=pending,
        completed_bookings=completed,
        total_earned=total_earned,
        pending_payout=pending_payout,
        average_rating=avg_rating,
        unread_notifications=unread,
    )


@router.get("/vendor/earnings-trend", response_model=TrendData)
async def vendor_earnings_trend(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    months = _last_n_months(6)
    start = datetime(months[0][0], months[0][1], 1, tzinfo=timezone.utc)
    rows = (
        await db.execute(
            select(EarningTxn.date, EarningTxn.amount).where(
                EarningTxn.vendor_id == vendor.id,
                EarningTxn.type == TxnType.earning,
                EarningTxn.date >= start,
            )
        )
    ).all()
    points = _bucket_by_month([(r.date, r.amount) for r in rows], months)
    return TrendData(points=points)
