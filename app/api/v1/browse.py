import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.booking import Booking, BookingSource, BookingStatus
from app.models.cms import Category
from app.models.event import EventStatus, PlatformEvent
from app.models.notification import IconKind, Notification
from app.models.user import ApprovalStatus, User
from app.models.vendor import Vendor
from app.schemas.browse import BrowseCategoryOut, InquiryCreate, InquiryOut, TickerItem
from app.schemas.vendor import VendorPublicOut

router = APIRouter(prefix="/browse", tags=["browse"])

_CATEGORY_FILTERS: dict[str, list[str]] = {
    "models": ["All", "Fashion", "Ethnic", "Ramp", "Film", "Commercial", "Fitness"],
    "photography": ["All", "Fashion", "Wedding", "Commercial", "Portrait"],
    "videography": ["All", "Brand Films", "Wedding", "Social Media", "Documentary"],
    "venues": ["All", "Indoor", "Outdoor", "Rooftop", "Heritage"],
    "event-services": ["All", "Fashion Shows", "Corporate", "Wedding Events", "Concerts"],
}


@router.get("/categories", response_model=list[BrowseCategoryOut])
async def browse_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.active == True).order_by(Category.sort_order))
    cats = result.scalars().all()
    return [
        BrowseCategoryOut(
            id=c.id,
            name=c.name,
            slug=c.slug,
            icon=c.icon,
            count=c.listings,
            filters=_CATEGORY_FILTERS.get(c.slug, ["All"]),
        )
        for c in cats
    ]


@router.get("/listings", response_model=list[VendorPublicOut])
async def browse_listings(
    category: str | None = None,
    city: str | None = None,
    filter: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Vendor).where(Vendor.status == ApprovalStatus.approved)
    if category:
        q = q.where(Vendor.category.ilike(f"%{category}%"))
    if city:
        # Include vendors in the requested city OR vendors with no city set (pan-India)
        from sqlalchemy import or_
        q = q.where(or_(Vendor.city.ilike(f"%{city}%"), Vendor.city == "", Vendor.city.is_(None)))
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()


@router.get("/ticker", response_model=list[TickerItem])
async def get_ticker(db: AsyncSession = Depends(get_db)):
    """Live scroll ticker items — active events with on_poster=True."""
    result = await db.execute(
        select(PlatformEvent)
        .where(PlatformEvent.on_poster == True, PlatformEvent.status.in_([EventStatus.live, EventStatus.upcoming]))
        .order_by(PlatformEvent.date.asc())
        .limit(10)
    )
    events = result.scalars().all()
    return [
        TickerItem(
            id=e.id,
            title=e.title,
            category=e.category,
            city=e.city,
            date=e.date.strftime("%d %b %Y"),
            on_poster=e.on_poster,
        )
        for e in events
    ]


@router.post("/inquiry", response_model=InquiryOut, status_code=201)
async def submit_inquiry(body: InquiryCreate, db: AsyncSession = Depends(get_db)):
    """
    Persists the inquiry as a Booking (status=requested, source=inquiry) and
    creates a Notification for the vendor. The AO9-XXXXXX ref is generated
    client-side so it appears immediately in the user app before the round-trip.
    """
    # Resolve vendor — fall back gracefully if vendor_id is unknown
    vendor_result = await db.execute(select(Vendor).where(Vendor.id == body.vendor_id))
    vendor = vendor_result.scalar_one_or_none()

    # Resolve or create a guest user record for the inquirer
    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()
    if not user:
        from app.core.security import hash_password
        import uuid
        user = User(
            id=f"U-{uuid.uuid4().hex[:8].upper()}",
            name=body.name,
            email=body.email,
            phone=body.phone,
            password_hash=hash_password(uuid.uuid4().hex),  # random — guest account
            status=ApprovalStatus.approved,
        )
        db.add(user)
        await db.flush()

    # Parse preferred date — default to 7 days from now
    try:
        preferred_date = datetime.fromisoformat(body.date)
    except (ValueError, TypeError):
        preferred_date = datetime.now(timezone.utc) + timedelta(days=7)

    # Create the Booking record
    booking = Booking(
        client_id=user.id,
        vendor_id=body.vendor_id if vendor else body.vendor_id,
        service=f"{body.category} — {body.message[:80]}" if body.message else body.category,
        date=preferred_date,
        amount=0.0,
        status=BookingStatus.requested,
        source=BookingSource.inquiry,
        inquiry_ref=body.inquiry_ref,
        location=body.phone,  # store phone in location for guest users
        notes=body.message,
    )
    db.add(booking)

    # Notify the vendor
    if vendor:
        notif = Notification(
            vendor_id=body.vendor_id,
            title="New inquiry received",
            body=f"{body.name} sent an inquiry ({body.inquiry_ref}){' — URGENT' if body.urgent else ''}",
            kind=IconKind.booking,
            unread=True,
        )
        db.add(notif)

    await db.commit()

    return InquiryOut(
        inquiry_ref=body.inquiry_ref,
        vendor_id=body.vendor_id,
        status="submitted",
        message=f"Your inquiry (ref: {body.inquiry_ref}) has been sent to the vendor.",
    )
