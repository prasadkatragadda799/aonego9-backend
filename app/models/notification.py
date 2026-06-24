import uuid
from datetime import datetime, timezone

import enum as _enum
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IconKind(_enum.Enum):
    booking = "booking"
    payment = "payment"
    review = "review"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"N-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[IconKind] = mapped_column(Enum(IconKind), default=IconKind.system)
    unread: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    vendor = relationship("Vendor", back_populates="notifications")
