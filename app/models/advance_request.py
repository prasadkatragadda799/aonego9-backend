import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AdvancePaymentRequest(Base):
    """User-submitted advance payment with receipt — pending superadmin approval."""
    __tablename__ = "advance_payment_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"ADV-{uuid.uuid4().hex[:8].upper()}")
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float, default=5000.0)
    receipt_image: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    admin_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking")
    user = relationship("User")
