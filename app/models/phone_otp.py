from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PhoneOtp(Base):
    __tablename__ = "phone_otps"

    phone: Mapped[str] = mapped_column(String(30), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(30), primary_key=True)  # register | inquiry
    code: Mapped[str] = mapped_column(String(6))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
