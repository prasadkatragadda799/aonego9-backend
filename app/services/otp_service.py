from datetime import datetime, timedelta, timezone
import random

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.phone_otp import PhoneOtp


def _normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    return phone.strip()


async def send_otp(db: AsyncSession, *, phone: str, purpose: str) -> dict:
    normalized = _normalize_phone(phone)
    if len(normalized) < 10:
        raise ValueError("Invalid phone number")
    code = f"{random.randint(0, 999999):06d}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.execute(delete(PhoneOtp).where(PhoneOtp.phone == normalized, PhoneOtp.purpose == purpose))
    db.add(PhoneOtp(phone=normalized, purpose=purpose, code=code, expires_at=expires))
    await db.commit()
    out: dict = {"ok": True, "phone": normalized, "expires_in_seconds": 600}
    if not settings.is_production or settings.OTP_DEBUG:
        out["debug_code"] = code
    return out


async def verify_otp(db: AsyncSession, *, phone: str, purpose: str, code: str) -> bool:
    normalized = _normalize_phone(phone)
    result = await db.execute(
        select(PhoneOtp).where(PhoneOtp.phone == normalized, PhoneOtp.purpose == purpose)
    )
    row = result.scalar_one_or_none()
    if not row:
        return False
    if row.code != code.strip():
        return False
    if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return False
    await db.execute(delete(PhoneOtp).where(PhoneOtp.phone == normalized, PhoneOtp.purpose == purpose))
    await db.commit()
    return True
