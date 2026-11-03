"""Vendor <-> client conversations."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ChatMessage, ChatThread
from app.models.notification import IconKind, Notification
from app.models.user import User


async def open_inquiry_thread(db: AsyncSession, *, vendor_id: str, client: User, text: str) -> ChatThread:
    """One thread per vendor+client; a new inquiry adds a message to it."""
    thread = (await db.execute(
        select(ChatThread).where(ChatThread.vendor_id == vendor_id, ChatThread.participant_id == client.id)
    )).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if thread is None:
        thread = ChatThread(vendor_id=vendor_id, participant_id=client.id, participant_name=client.name or "Client", unread_count=0)
        db.add(thread)
        await db.flush()
    db.add(ChatMessage(thread_id=thread.id, text=text[:4000], from_vendor=False, sent_at=now))
    thread.last_message = text[:4000]
    thread.last_message_at = now
    thread.unread_count = (thread.unread_count or 0) + 1
    return thread


def notify_vendor_of_message(db: AsyncSession, thread: ChatThread, text: str) -> None:
    db.add(Notification(
        vendor_id=thread.vendor_id,
        title=f"New message from {thread.participant_name or 'a client'}",
        body=text[:200],
        kind=IconKind.system,
        unread=True,
    ))
