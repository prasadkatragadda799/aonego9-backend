import uuid
from datetime import datetime, timezone

import enum as _enum
from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventStatus(_enum.Enum):
    draft = "draft"
    upcoming = "upcoming"
    live = "live"
    ended = "ended"


class PlatformEvent(Base):
    __tablename__ = "platform_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"EV-{uuid.uuid4().hex[:8].upper()}")
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.upcoming)
    on_poster: Mapped[bool] = mapped_column(Boolean, default=False)
    registrations: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
