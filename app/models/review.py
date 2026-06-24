import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"R-{uuid.uuid4().hex[:8].upper()}")
    author_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    booking_id: Mapped[str | None] = mapped_column(String, ForeignKey("bookings.id"), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=5)
    text: Mapped[str] = mapped_column(Text, default="")
    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    author = relationship("User", back_populates="reviews", foreign_keys=[author_id])
    vendor = relationship("Vendor", back_populates="reviews", foreign_keys=[vendor_id])
    booking = relationship("Booking")
