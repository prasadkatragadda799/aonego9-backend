from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_any_authenticated, get_current_admin, get_current_user, get_current_vendor
from app.models.advance_request import AdvancePaymentRequest
from app.models.booking import Booking, BookingSource, BookingStatus
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.booking import (
    AdvancePayment,
    AdvanceRequestOut,
    AdvanceReview,
    BookingCreate,
    BookingListOut,
    BookingOut,
    BookingStatusUpdate,
)
from app.utils.admin_scope import vendor_city_clause

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


def _advance_out(
    row: AdvancePaymentRequest,
    *,
    client_name: str = "",
    vendor_name: str = "",
    inquiry_ref: str | None = None,
) -> AdvanceRequestOut:
    return AdvanceRequestOut(
        id=row.id,
        booking_id=row.booking_id,
        user_id=row.user_id,
        client_name=client_name,
        vendor_name=vendor_name,
        inquiry_ref=inquiry_ref,
        amount=row.amount,
        receipt_image=row.receipt_image,
        status=row.status,
        admin_note=row.admin_note,
        created_at=row.created_at,
        reviewed_at=row.reviewed_at,
    )


async def _advance_context(
    db: AsyncSession, rows: list[AdvancePaymentRequest]
) -> tuple[dict[str, str], dict[str, str], dict[str, Booking]]:
    if not rows:
        return {}, {}, {}
    booking_ids = {r.booking_id for r in rows}
    bookings_result = await db.execute(select(Booking).where(Booking.id.in_(booking_ids)))
    bookings = {b.id: b for b in bookings_result.scalars().all()}
    client_ids = {b.client_id for b in bookings.values()}
    vendor_ids = {b.vendor_id for b in bookings.values()}
    client_names: dict[str, str] = {}
    vendor_names: dict[str, str] = {}
    if client_ids:
        cr = await db.execute(select(User.id, User.name).where(User.id.in_(client_ids)))
        client_names = {row.id: row.name for row in cr}
    if vendor_ids:
        vr = await db.execute(select(Vendor.id, Vendor.name).where(Vendor.id.in_(vendor_ids)))
        vendor_names = {row.id: row.name for row in vr}
    return client_names, vendor_names, bookings


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


@router.get("/admin", response_model=BookingListOut)
async def admin_list_bookings(
    status: str | None = None,
    source: str | None = None,
    city: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Booking)
    scoped_city = (admin.admin_city or "").strip() or (city or "").strip()
    if scoped_city:
        q = q.join(Vendor, Booking.vendor_id == Vendor.id).where(Vendor.city.ilike(f"%{scoped_city}%"))
    elif city:
        q = q.join(Vendor, Booking.vendor_id == Vendor.id).where(Vendor.city.ilike(f"%{city.strip()}%"))
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


@router.post("/advance", response_model=AdvanceRequestOut, status_code=201)
async def request_advance(
    body: AdvancePayment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit advance payment with receipt — pending superadmin approval."""
    if not body.receipt_image.strip():
        raise HTTPException(status_code=422, detail="Receipt image is required")
    result = await db.execute(select(Booking).where(Booking.id == body.booking_id, Booking.client_id == current_user.id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    pending = await db.execute(
        select(AdvancePaymentRequest).where(
            AdvancePaymentRequest.booking_id == body.booking_id,
            AdvancePaymentRequest.status == "pending",
        )
    )
    if pending.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An advance request is already pending for this booking")
    row = AdvancePaymentRequest(
        booking_id=body.booking_id,
        user_id=current_user.id,
        amount=body.amount,
        receipt_image=body.receipt_image.strip(),
        status="pending",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _advance_out(
        row,
        client_name=client_names.get(booking.client_id, ""),
        vendor_name=vendor_names.get(booking.vendor_id, ""),
        inquiry_ref=booking.inquiry_ref,
    )


@router.get("/advance/mine", response_model=list[AdvanceRequestOut])
async def my_advance_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdvancePaymentRequest)
        .where(AdvancePaymentRequest.user_id == current_user.id)
        .order_by(AdvancePaymentRequest.created_at.desc())
    )
    rows = result.scalars().all()
    client_names, vendor_names, bookings = await _advance_context(db, rows)
    return [
        _advance_out(
            r,
            client_name=client_names.get(r.user_id, current_user.name),
            vendor_name=vendor_names.get(bookings[r.booking_id].vendor_id, "") if r.booking_id in bookings else "",
            inquiry_ref=bookings[r.booking_id].inquiry_ref if r.booking_id in bookings else None,
        )
        for r in rows
    ]


@router.get("/admin/advance", response_model=list[AdvanceRequestOut])
async def admin_list_advance_requests(
    status: str | None = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(AdvancePaymentRequest).order_by(AdvancePaymentRequest.created_at.desc())
    if status:
        q = q.where(AdvancePaymentRequest.status == status)
    result = await db.execute(q)
    rows = result.scalars().all()
    client_names, vendor_names, bookings = await _advance_context(db, rows)
    if admin.admin_city.strip():
        allowed_vendor_ids = set()
        vr = await db.execute(select(Vendor.id).where(vendor_city_clause(admin, Vendor.city)))
        allowed_vendor_ids = {row.id for row in vr}
        rows = [r for r in rows if r.booking_id in bookings and bookings[r.booking_id].vendor_id in allowed_vendor_ids]
    return [
        _advance_out(
            r,
            client_name=client_names.get(bookings[r.booking_id].client_id, "") if r.booking_id in bookings else "",
            vendor_name=vendor_names.get(bookings[r.booking_id].vendor_id, "") if r.booking_id in bookings else "",
            inquiry_ref=bookings[r.booking_id].inquiry_ref if r.booking_id in bookings else None,
        )
        for r in rows
    ]


@router.post("/admin/advance/{request_id}/approve", response_model=AdvanceRequestOut)
async def admin_approve_advance(
    request_id: str,
    body: AdvanceReview,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdvancePaymentRequest).where(AdvancePaymentRequest.id == request_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Advance request not found")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail=f"Request already {row.status}")
    booking_result = await db.execute(select(Booking).where(Booking.id == row.booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if admin.admin_city.strip():
        vendor_result = await db.execute(select(Vendor).where(Vendor.id == booking.vendor_id))
        vendor = vendor_result.scalar_one_or_none()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        scoped = admin.admin_city.strip().lower()
        vcity = (vendor.city or "").lower()
        if scoped and vcity and scoped not in vcity and vcity not in scoped:
            raise HTTPException(status_code=403, detail="Not in your city scope")
    booking.advance_paid += row.amount
    row.status = "approved"
    row.admin_note = body.admin_note
    row.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    client_names, vendor_names = await _name_lookups(db, [booking])
    return _advance_out(
        row,
        client_name=client_names.get(booking.client_id, ""),
        vendor_name=vendor_names.get(booking.vendor_id, ""),
        inquiry_ref=booking.inquiry_ref,
    )


@router.post("/admin/advance/{request_id}/reject", response_model=AdvanceRequestOut)
async def admin_reject_advance(
    request_id: str,
    body: AdvanceReview,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdvancePaymentRequest).where(AdvancePaymentRequest.id == request_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Advance request not found")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail=f"Request already {row.status}")
    row.status = "rejected"
    row.admin_note = body.admin_note
    row.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    booking_result = await db.execute(select(Booking).where(Booking.id == row.booking_id))
    booking = booking_result.scalar_one_or_none()
    client_names, vendor_names = await _name_lookups(db, [booking] if booking else [])
    return _advance_out(
        row,
        client_name=client_names.get(booking.client_id, "") if booking else "",
        vendor_name=vendor_names.get(booking.vendor_id, "") if booking else "",
        inquiry_ref=booking.inquiry_ref if booking else None,
    )
