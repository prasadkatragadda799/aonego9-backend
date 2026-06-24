import random
import string
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.cms import Category
from app.models.event import EventStatus, PlatformEvent
from app.models.user import ApprovalStatus
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
        q = q.where(Vendor.city == city)
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
async def submit_inquiry(body: InquiryCreate):
    """
    Stateless inquiry submission — the Flutter app generates the AO9-XXXXXX ref
    client-side and passes it here. The backend records it and forwards a
    booking-request notification to the vendor (notification creation omitted
    here; wire it to your notification service).
    """
    return InquiryOut(
        inquiry_ref=body.inquiry_ref,
        vendor_id=body.vendor_id,
        status="submitted",
        message=f"Your inquiry (ref: {body.inquiry_ref}) has been sent to the vendor.",
    )
