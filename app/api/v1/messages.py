from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_vendor
from app.models.message import ChatMessage, ChatThread
from app.models.vendor import Vendor
from app.schemas.message import ChatThreadDetailOut, ChatThreadOut, SendMessageRequest

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/threads", response_model=list[ChatThreadOut])
async def list_threads(
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.vendor_id == vendor.id)
        .order_by(ChatThread.last_message_at.desc())
    )
    return result.scalars().all()


@router.get("/threads/{thread_id}", response_model=ChatThreadDetailOut)
async def get_thread(
    thread_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.id == thread_id, ChatThread.vendor_id == vendor.id)
        .options(selectinload(ChatThread.messages))
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread.unread_count = 0
    await db.commit()
    return thread


@router.post("/threads/{thread_id}/messages", status_code=201)
async def send_message(
    thread_id: str,
    body: SendMessageRequest,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatThread).where(ChatThread.id == thread_id, ChatThread.vendor_id == vendor.id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    msg = ChatMessage(thread_id=thread_id, text=body.text, from_vendor=True)
    thread.last_message = body.text
    thread.last_message_at = datetime.now(timezone.utc)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
