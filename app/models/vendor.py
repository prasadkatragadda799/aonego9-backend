import uuid
from datetime import datetime, timezone

import enum as _enum
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import ApprovalStatus


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"V-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(80), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.pending)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    plan: Mapped[str] = mapped_column(String(20), default="Starter")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    packages = relationship("ServicePackage", back_populates="vendor", cascade="all, delete-orphan")
    roster = relationship("TalentMember", back_populates="vendor", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="vendor", foreign_keys="Booking.vendor_id")
    earnings = relationship("EarningTxn", back_populates="vendor")
    reviews = relationship("Review", back_populates="vendor", foreign_keys="Review.vendor_id")
    chat_threads = relationship("ChatThread", back_populates="vendor")
    notifications = relationship("Notification", back_populates="vendor")
    subscription = relationship("VendorSubscription", back_populates="vendor", uselist=False)
    billing_entries = relationship("BillingEntry", back_populates="vendor")


class ServicePackage(Base):
    __tablename__ = "service_packages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"P-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    bookings_count: Mapped[int] = mapped_column(Integer, default=0)

    vendor = relationship("Vendor", back_populates="packages")


class TalentMember(Base):
    __tablename__ = "talent_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"M-{uuid.uuid4().hex[:8].upper()}")
    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(80), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    day_rate: Mapped[float] = mapped_column(Float, default=0.0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    shoots: Mapped[int] = mapped_column(Integer, default=0)
    avatar_url: Mapped[str] = mapped_column(String(500), default="")

    vendor = relationship("Vendor", back_populates="roster")
