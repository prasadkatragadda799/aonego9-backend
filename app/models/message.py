import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"TH-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    participant_name: Mapped[str] = mapped_column(String(120), default="")
    participant_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    last_message: Mapped[str] = mapped_column(Text, default="")
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    unread_count: Mapped[int] = mapped_column(Integer, default=0)

    vendor = relationship("Vendor", back_populates="chat_threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan", order_by="ChatMessage.sent_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"MSG-{uuid.uuid4().hex[:8].upper()}")
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("chat_threads.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    from_vendor: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    thread = relationship("ChatThread", back_populates="messages")
