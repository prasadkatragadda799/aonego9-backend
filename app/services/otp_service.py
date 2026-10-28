from datetime import datetime, timedelta, timezone
import random
import secrets
import time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.phone_otp import PhoneOtp

# Per-process send throttle (best-effort; use Redis in multi-worker prod).
_otp_send_log: dict[str, list[float]] = {}


def _enforce_otp_rate_limit(phone: str) -> None:
    now = time.time()
    window = _otp_send_log.setdefault(phone, [])
    window[:] = [t for t in window if now - t < 3600]
    if len(window) >= 5:
        raise ValueError("Too many OTP requests — try again in an hour")
    if window and now - window[-1] < 60:
        raise ValueError("Wait a minute before requesting another OTP")
    window.append(now)


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
    _enforce_otp_rate_limit(normalized)
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
    if not secrets.compare_digest(row.code, code.strip()):
        return False
    if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return False
    await db.execute(delete(PhoneOtp).where(PhoneOtp.phone == normalized, PhoneOtp.purpose == purpose))
    await db.commit()
    return True
