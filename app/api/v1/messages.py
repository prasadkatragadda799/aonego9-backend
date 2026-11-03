from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_vendor
from app.models.message import ChatMessage, ChatThread
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.message import ChatMessageOut, ChatThreadDetailOut, ChatThreadOut, SendMessageRequest
from app.services.messaging import notify_vendor_of_message

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
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    msg = ChatMessage(thread_id=thread_id, text=text[:4000], from_vendor=True)
    thread.last_message = text[:4000]
    thread.last_message_at = datetime.now(timezone.utc)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


# ── Client side ───────────────────────────────────────────────────
# The same conversations, seen by the signed-in client in the user app.
# Threads open automatically when the client sends an inquiry.


class ClientThreadOut(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    last_message: str
    last_message_at: datetime
    messages: list[ChatMessageOut] = []


async def _client_threads(db: AsyncSession, user: User, thread_id: str | None = None):
    q = select(ChatThread).options(selectinload(ChatThread.messages)).where(ChatThread.participant_id == user.id)
    if thread_id:
        q = q.where(ChatThread.id == thread_id)
    threads = (await db.execute(q.order_by(ChatThread.last_message_at.desc()))).scalars().all()
    vendor_ids = {t.vendor_id for t in threads}
    names: dict[str, str] = {}
    if vendor_ids:
        rows = await db.execute(select(Vendor).where(Vendor.id.in_(vendor_ids)))
        names = {v.id: (v.company or v.name) for v in rows.scalars().all()}
    return threads, names


@router.get("/me/threads", response_model=list[ClientThreadOut])
async def client_threads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    threads, names = await _client_threads(db, user)
    return [
        ClientThreadOut(id=t.id, vendor_id=t.vendor_id, vendor_name=names.get(t.vendor_id, "Vendor"),
                        last_message=t.last_message, last_message_at=t.last_message_at)
        for t in threads
    ]


@router.get("/me/threads/{thread_id}", response_model=ClientThreadOut)
async def client_thread(thread_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    threads, names = await _client_threads(db, user, thread_id)
    if not threads:
        raise HTTPException(status_code=404, detail="Conversation not found")
    t = threads[0]
    return ClientThreadOut(
        id=t.id, vendor_id=t.vendor_id, vendor_name=names.get(t.vendor_id, "Vendor"),
        last_message=t.last_message, last_message_at=t.last_message_at,
        messages=[ChatMessageOut.model_validate(m) for m in t.messages],
    )


@router.post("/me/threads/{thread_id}/messages", response_model=ChatMessageOut, status_code=201)
async def client_send(
    thread_id: str,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    thread = (await db.execute(
        select(ChatThread).where(ChatThread.id == thread_id, ChatThread.participant_id == user.id)
    )).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Conversation not found")
    now = datetime.now(timezone.utc)
    msg = ChatMessage(thread_id=thread.id, text=text[:4000], from_vendor=False, sent_at=now)
    db.add(msg)
    thread.last_message = text[:4000]
    thread.last_message_at = now
    thread.unread_count = (thread.unread_count or 0) + 1
    notify_vendor_of_message(db, thread, text)
    await db.commit()
    await db.refresh(msg)
    return msg
