from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_any_authenticated, get_current_admin, get_current_user, get_current_vendor
from app.models.booking import Booking, BookingSource, BookingStatus
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.booking import (
    AdvancePayment,
    BookingCreate,
    BookingListOut,
    BookingOut,
    BookingStatusUpdate,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])

_VALID_STATUS_TRANSITIONS: dict[BookingStatus, list[BookingStatus]] = {
    BookingStatus.requested: [BookingStatus.confirmed, BookingStatus.cancelled],
    BookingStatus.confirmed: [BookingStatus.in_progress, BookingStatus.cancelled],
    BookingStatus.in_progress: [BookingStatus.completed, BookingStatus.disputed],
    BookingStatus.completed: [],
    BookingStatus.cancelled: [],
    BookingStatus.disputed: [BookingStatus.completed, BookingStatus.cancelled],
}


def _to_out(b: Booking, client_name: str = "", vendor_name: str = "") -> BookingOut:
    return BookingOut(
        id=b.id,
        client_id=b.client_id,
        client_name=client_name,
        vendor_id=b.vendor_id,
        vendor_name=vendor_name,
        service=b.service,
        package_id=b.package_id,
        date=b.date,
        amount=b.amount,
        advance_paid=b.advance_paid,
        balance_due=max(0.0, b.amount - b.advance_paid),
        status=b.status.value,
        source=b.source.value,
        inquiry_ref=b.inquiry_ref,
        location=b.location,
        notes=b.notes,
        created_at=b.created_at,
    )


async def _name_lookups(db: AsyncSession, bookings: list[Booking]) -> tuple[dict[str, str], dict[str, str]]:
    """Batch-resolve client/vendor display names for a page of bookings (avoids N+1 queries)."""
    client_ids = {b.client_id for b in bookings}
    vendor_ids = {b.vendor_id for b in bookings}
    client_names: dict[str, str] = {}
    vendor_names: dict[str, str] = {}
    if client_ids:
        rows = await db.execute(select(User.id, User.name).where(User.id.in_(client_ids)))
        client_names = {row.id: row.name for row in rows}
    if vendor_ids:
        rows = await db.execute(select(Vendor.id, Vendor.name).where(Vendor.id.in_(vendor_ids)))
        vendor_names = {row.id: row.name for row in rows}
    return client_names, vendor_names


@router.post("", response_model=BookingOut, status_code=201)
async def create_booking(
    body: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = Booking(
        client_id=current_user.id,
        vendor_id=body.vendor_id,
        service=body.service,
        package_id=body.package_id,
        date=body.date,
        amount=body.amount,
        location=body.location,
        notes=body.notes,
        source=BookingSource(body.source),
        inquiry_ref=body.inquiry_ref,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _to_out(booking, client_names.get(booking.client_id, ""), vendor_names.get(booking.vendor_id, ""))


@router.get("/vendor", response_model=BookingListOut)
async def list_vendor_bookings(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    q = select(Booking).where(Booking.vendor_id == vendor.id)
    if status:
        q = q.where(Booking.status == BookingStatus(status))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.order_by(Booking.date.desc()).offset((page - 1) * page_size).limit(page_size))
    bookings = result.scalars().all()
    client_names, vendor_names = await _name_lookups(db, bookings)
    return BookingListOut(
        items=[_to_out(b, client_names.get(b.client_id, ""), vendor_names.get(b.vendor_id, "")) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/vendor/calendar")
async def vendor_calendar(
    year: int = Query(...),
    month: int = Query(...),
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    from calendar import monthrange
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, monthrange(year, month)[1], 23, 59, 59, tzinfo=timezone.utc)
    result = await db.execute(
        select(Booking).where(
            Booking.vendor_id == vendor.id,
            Booking.date >= start,
            Booking.date <= end,
        )
    )
    bookings = result.scalars().all()
    client_names, vendor_names = await _name_lookups(db, bookings)
    return [_to_out(b, client_names.get(b.client_id, ""), vendor_names.get(b.vendor_id, "")) for b in bookings]


@router.get("/me", response_model=BookingListOut)
async def list_user_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Booking).where(Booking.client_id == current_user.id)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.order_by(Booking.date.desc()).offset((page - 1) * page_size).limit(page_size))
    bookings = result.scalars().all()
    client_names, vendor_names = await _name_lookups(db, bookings)
    return BookingListOut(
        items=[_to_out(b, client_names.get(b.client_id, ""), vendor_names.get(b.vendor_id, "")) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin", response_model=BookingListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_bookings(
    status: str | None = None,
    source: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Booking)
    if status:
        q = q.where(Booking.status == BookingStatus(status))
    if source:
        q = q.where(Booking.source == BookingSource(source))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.order_by(Booking.date.desc()).offset((page - 1) * page_size).limit(page_size))
    bookings = result.scalars().all()
    client_names, vendor_names = await _name_lookups(db, bookings)
    return BookingListOut(
        items=[_to_out(b, client_names.get(b.client_id, ""), vendor_names.get(b.vendor_id, "")) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: str,
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    role = payload.get("role")
    sub = payload.get("sub")
    if role == "user" and booking.client_id != sub:
        raise HTTPException(status_code=403, detail="Not your booking")
    if role == "vendor" and booking.vendor_id != sub:
        raise HTTPException(status_code=403, detail="Not your booking")
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _to_out(booking, client_names.get(booking.client_id, ""), vendor_names.get(booking.vendor_id, ""))


@router.put("/{booking_id}/status", response_model=BookingOut)
async def update_booking_status(
    booking_id: str,
    body: BookingStatusUpdate,
    payload: dict = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    new_status = BookingStatus(body.status)
    allowed = _VALID_STATUS_TRANSITIONS.get(booking.status, [])
    if new_status not in allowed and payload.get("role") != "admin":
        raise HTTPException(status_code=422, detail=f"Cannot transition from {booking.status.value} to {body.status}")
    booking.status = new_status
    booking.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(booking)
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _to_out(booking, client_names.get(booking.client_id, ""), vendor_names.get(booking.vendor_id, ""))


@router.post("/advance", response_model=BookingOut)
async def pay_advance(
    body: AdvancePayment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == body.booking_id, Booking.client_id == current_user.id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.advance_paid += body.amount
    await db.commit()
    await db.refresh(booking)
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _to_out(booking, client_names.get(booking.client_id, ""), vendor_names.get(booking.vendor_id, ""))
