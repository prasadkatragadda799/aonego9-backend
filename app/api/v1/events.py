from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.event import EventStatus, PlatformEvent
from app.models.user import User
from app.schemas.event import (
    EventListOut,
    PlatformEventCreate,
    PlatformEventOut,
    PlatformEventUpdate,
    PosterToggle,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[PlatformEventOut])
async def list_public_events(db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns live and upcoming events for the user app ticker."""
    result = await db.execute(
        select(PlatformEvent)
        .where(PlatformEvent.status.in_([EventStatus.live, EventStatus.upcoming]))
        .order_by(PlatformEvent.date.asc())
    )
    return result.scalars().all()


@router.get("/admin", response_model=EventListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_events(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(PlatformEvent)
    if status:
        q = q.where(PlatformEvent.status == EventStatus(status))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(PlatformEvent.date.asc()).offset((page - 1) * page_size).limit(page_size))
    return EventListOut(items=result.scalars().all(), total=total)


@router.post("/admin", response_model=PlatformEventOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_event(body: PlatformEventCreate, db: AsyncSession = Depends(get_db)):
    event = PlatformEvent(
        title=body.title,
        category=body.category,
        city=body.city,
        date=body.date,
        status=EventStatus(body.status),
        on_poster=body.on_poster,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.put("/admin/{event_id}", response_model=PlatformEventOut)
async def update_event(
    event_id: str,
    body: PlatformEventUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(PlatformEvent).where(PlatformEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    updates = body.model_dump(exclude_none=True)
    if "status" in updates:
        updates["status"] = EventStatus(updates["status"])
    for field, value in updates.items():
        setattr(event, field, value)
    await db.commit()
    await db.refresh(event)
    return event


@router.patch("/admin/{event_id}/poster", response_model=PlatformEventOut)
async def toggle_poster(
    event_id: str,
    body: PosterToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(PlatformEvent).where(PlatformEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.on_poster = body.on_poster
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/admin/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(PlatformEvent).where(PlatformEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
