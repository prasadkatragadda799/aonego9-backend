from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_vendor
from app.models.notification import Notification
from app.models.vendor import Vendor
from app.schemas.notification import NotificationListOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.vendor_id == vendor.id)
        .order_by(Notification.created_at.desc())
    )
    items = result.scalars().all()
    unread = sum(1 for n in items if n.unread)
    return NotificationListOut(items=items, unread_count=unread)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.vendor_id == vendor.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.unread = False
    await db.commit()
    await db.refresh(notif)
    return notif


@router.post("/mark-all-read")
async def mark_all_read(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.vendor_id == vendor.id, Notification.unread == True)
        .values(unread=False)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}
