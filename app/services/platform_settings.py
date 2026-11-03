"""Platform settings (commission, KYC and payout rules) with defaults."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_setting import PlatformSetting

PLATFORM_DEFAULTS: dict = {
    "commission_percent": 15,
    "auto_approve_kyc": False,
    "email_alerts": True,
    "payout_hold_hours": 48,
}


async def load_platform_settings(db: AsyncSession) -> dict:
    rows = (await db.execute(select(PlatformSetting))).scalars().all()
    data = dict(PLATFORM_DEFAULTS)
    for r in rows:
        try:
            data[r.key] = json.loads(r.value_json)
        except json.JSONDecodeError:
            pass
    return data
