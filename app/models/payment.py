import uuid
from datetime import datetime, timezone

import enum as _enum
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentStatus(_enum.Enum):
    pending = "pending"
    paid = "paid"
    refunded = "refunded"
    failed = "failed"
    payout = "payout"


class TxnType(_enum.Enum):
    earning = "earning"
    payout = "payout"
    refund = "refund"
    subscription = "subscription"
    advance = "advance"
    commission = "commission"
    booking = "booking"


class PaymentTxn(Base):
    """Platform-level payment transaction (superadmin view)."""
    __tablename__ = "payment_txns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"T-{uuid.uuid4().hex[:8].upper()}")
    booking_id: Mapped[str | None] = mapped_column(String, ForeignKey("bookings.id"), nullable=True, index=True)
    party: Mapped[str] = mapped_column(String(200), default="")
    type: Mapped[TxnType] = mapped_column(Enum(TxnType), default=TxnType.booking)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending)
    method: Mapped[str] = mapped_column(String(50), default="")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    booking = relationship("Booking")


class EarningTxn(Base):
    """Vendor-side earning/payout ledger entry."""
    __tablename__ = "earning_txns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"E-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    booking_id: Mapped[str | None] = mapped_column(String, ForeignKey("bookings.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(200), default="")
    type: Mapped[TxnType] = mapped_column(Enum(TxnType), default=TxnType.earning)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    vendor = relationship("Vendor", back_populates="earnings")
    booking = relationship("Booking")
