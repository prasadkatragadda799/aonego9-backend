import uuid
from datetime import datetime, timezone

import enum as _enum
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookingStatus(_enum.Enum):
    requested = "requested"
    confirmed = "confirmed"
    in_progress = "inProgress"
    completed = "completed"
    cancelled = "cancelled"
    disputed = "disputed"


class BookingSource(_enum.Enum):
    direct = "direct"
    inquiry = "inquiry"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"B-{uuid.uuid4().hex[:8].upper()}")
    client_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    service: Mapped[str] = mapped_column(String(200), default="")
    package_id: Mapped[str | None] = mapped_column(String, ForeignKey("service_packages.id"), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    advance_paid: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.requested)
    source: Mapped[BookingSource] = mapped_column(Enum(BookingSource), default=BookingSource.direct)
    inquiry_ref: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    location: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    client = relationship("User", back_populates="bookings", foreign_keys=[client_id])
    vendor = relationship("Vendor", back_populates="bookings", foreign_keys=[vendor_id])
    package = relationship("ServicePackage")
