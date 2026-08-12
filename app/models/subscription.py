import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    period: Mapped[str] = mapped_column(String(30), default="per month")
    features: Mapped[str] = mapped_column(Text, default="")
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    # "vendor" | "user" | "both" — which app(s) this plan is offered to.
    audience: Mapped[str] = mapped_column(String(10), default="both")


class VendorSubscription(Base):
    __tablename__ = "vendor_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"SUB-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("subscription_plans.id"))
    plan_name: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    renews_on: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    vendor = relationship("Vendor", back_populates="subscription")
    plan = relationship("SubscriptionPlan")


class ClientSubscription(Base):
    __tablename__ = "client_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"SUB-{uuid.uuid4().hex[:8].upper()}")
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("subscription_plans.id"))
    plan_name: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    renews_on: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan")


class SubscriptionRequest(Base):
    """A user/vendor's claim of having paid for a plan via UPI, pending
    manual admin review of the uploaded receipt screenshot."""
    __tablename__ = "subscription_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"REQ-{uuid.uuid4().hex[:8].upper()}")
    requester_type: Mapped[str] = mapped_column(String(10))  # "vendor" | "user"
    vendor_id: Mapped[str | None] = mapped_column(String, ForeignKey("vendors.id"), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("subscription_plans.id"))
    plan_name: Mapped[str] = mapped_column(String(50), default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    # Base64 data URI of the payment screenshot — no file storage configured
    # on this backend today, so the receipt is kept inline in the row.
    receipt_image: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    admin_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vendor = relationship("Vendor")
    user = relationship("User")
    plan = relationship("SubscriptionPlan")


class PaymentSettings(Base):
    """Single-row table holding the platform's UPI collection details,
    used by client apps to render a pay-by-UPI QR code."""
    __tablename__ = "payment_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default="default")
    upi_id: Mapped[str] = mapped_column(String(100), default="")
    payee_name: Mapped[str] = mapped_column(String(100), default="AOneGo9")


class BillingEntry(Base):
    __tablename__ = "billing_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"INV-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    description: Mapped[str] = mapped_column(String(200), default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    vendor = relationship("Vendor", back_populates="billing_entries")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"S-{uuid.uuid4().hex[:8].upper()}")
    requester_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    requester = relationship("User", back_populates="support_tickets")
