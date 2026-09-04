import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.booking import Booking, BookingSource, BookingStatus
from app.models.cms import Category
from app.models.directory import AdCreative, Lead, LogoPartner, Session as SessionModel, TeamMember
from app.models.event import EventStatus, PlatformEvent
from app.models.newsletter import NewsletterContribution, NewsletterIssue
from app.models.notification import IconKind, Notification
from app.models.user import ApprovalStatus, User
from app.models.vendor import Vendor
from app.schemas.browse import BrowseCategoryOut, InquiryCreate, InquiryOut, TickerItem
from app.schemas.directory import (
    AdCreativeOut,
    LeadCreate,
    LeadOut,
    LeadStatusUpdate,
    LogoPartnerOut,
    TeamMemberOut,
    lead_from_create,
    lead_to_out,
)
from app.schemas.newsletter import NewsletterContributeIn, NewsletterIssueOut, NewsletterSubscribeIn
from app.schemas.vendor import VendorPublicOut
from app.schemas.vendor_serializers import vendor_to_public_out
from app.services.otp_service import verify_otp

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
    if filter and filter.lower() != "all":
        from sqlalchemy import or_
        q = q.where(or_(
            Vendor.bio.ilike(f"%{filter}%"),
            Vendor.category.ilike(f"%{filter}%"),
            Vendor.company.ilike(f"%{filter}%"),
        ))
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return [vendor_to_public_out(v) for v in result.scalars().all()]


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


@router.get("/newsletters", response_model=list[NewsletterIssueOut])
async def browse_newsletters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsletterIssue).order_by(NewsletterIssue.published_at.desc()))
    return [NewsletterIssueOut.from_row(r) for r in result.scalars().all()]


@router.post("/newsletter/subscribe", status_code=201)
async def subscribe_newsletter(body: NewsletterSubscribeIn, db: AsyncSession = Depends(get_db)):
    row = NewsletterContribution(
        name=body.name,
        email=body.email,
        phone=body.phone,
        city=body.city,
        organisation="",
        headline="Newsletter subscription",
        story="",
        status="subscribed",
    )
    db.add(row)
    await db.commit()
    return {"ok": True}


@router.post("/newsletter/contribute", status_code=201)
async def contribute_newsletter(body: NewsletterContributeIn, db: AsyncSession = Depends(get_db)):
    row = NewsletterContribution(
        name=body.name,
        email=body.email,
        phone=body.phone,
        city=body.city,
        organisation=body.organisation,
        headline=body.headline,
        story=body.story,
        credentials_url=body.credentials_url,
        status="pending",
    )
    db.add(row)
    await db.commit()
    return {"ok": True, "id": row.id}


@router.post("/inquiry", response_model=InquiryOut, status_code=201)
async def submit_inquiry(body: InquiryCreate, db: AsyncSession = Depends(get_db)):
    """
    Persists the inquiry as a Booking (status=requested, source=inquiry) and
    creates a Notification for the vendor. The AO9-XXXXXX ref is generated
    client-side so it appears immediately in the user app before the round-trip.
    """
    if body.phone.strip():
        if not body.phone_otp.strip():
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Phone OTP required before submitting an inquiry")
        if not await verify_otp(db, phone=body.phone, purpose="inquiry", code=body.phone_otp):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid or expired phone OTP")

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
    await db.flush()

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
    await db.refresh(booking)

    return InquiryOut(
        inquiry_ref=body.inquiry_ref,
        vendor_id=body.vendor_id,
        booking_id=booking.id,
        status="submitted",
        message=f"Your inquiry (ref: {body.inquiry_ref}) has been sent to the vendor.",
    )


# ── Directory content (public reads) ────────────────────────────

@router.get("/ads", response_model=list[AdCreativeOut])
async def browse_ads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdCreative).where(AdCreative.active == True))
    return result.scalars().all()


@router.get("/partners", response_model=list[LogoPartnerOut])
async def browse_partners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LogoPartner).where(LogoPartner.published == True))
    return result.scalars().all()


@router.get("/team", response_model=list[TeamMemberOut])
async def browse_team(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).where(TeamMember.published == True))
    return result.scalars().all()


@router.get("/updates")
async def browse_updates(db: AsyncSession = Depends(get_db)):
    """The notification bar feed — upcoming/live platform events plus
    published sessions, collapsed to one shape and sorted by date."""
    events_result = await db.execute(
        select(PlatformEvent).where(PlatformEvent.status.in_([EventStatus.upcoming, EventStatus.live]))
    )
    sessions_result = await db.execute(select(SessionModel).where(SessionModel.published == True))

    items = [
        {
            "id": e.id,
            "kind": "event",
            "division": "",
            "title": e.title,
            "city": e.city,
            "state": "",
            "date": e.date.isoformat(),
            "emoji": "🎪",
            "live": e.status == EventStatus.live or e.on_poster,
        }
        for e in events_result.scalars().all()
    ] + [
        {
            "id": s.id,
            "kind": s.mode,
            "division": s.division,
            "title": s.title,
            "city": s.city,
            "state": s.state,
            "date": s.date,
            "emoji": s.emoji,
            "live": s.seats > 0 and 0 < s.seats_left <= s.seats * 0.2,
        }
        for s in sessions_result.scalars().all()
    ]
    items.sort(key=lambda i: i["date"] or "")
    return items


# ── Leads (contact / join us / apply / session sign-up) ──────────

@router.post("/leads", response_model=LeadOut, status_code=201)
async def submit_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    row = lead_from_create(body)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return lead_to_out(row)


@router.get("/leads", response_model=list[LeadOut], dependencies=[Depends(get_current_admin)])
async def admin_list_leads(
    kind: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Lead)
    if kind:
        q = q.where(Lead.kind == kind)
    if status:
        q = q.where(Lead.status == status)
    result = await db.execute(q.order_by(Lead.created_at.desc()))
    return [lead_to_out(r) for r in result.scalars().all()]


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def admin_update_lead_status(
    lead_id: str,
    body: LeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    row.status = body.status
    await db.commit()
    await db.refresh(row)
    return lead_to_out(row)
