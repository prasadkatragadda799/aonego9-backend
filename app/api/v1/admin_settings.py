"""Platform settings and the admin team — the super admin console's Settings."""

import json
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.security import hash_password
from app.models.platform_setting import PlatformSetting
from app.models.user import ApprovalStatus, User
from app.models.vendor import Vendor
from app.services.platform_settings import load_platform_settings
from app.utils.admin_scope import admin_city

router = APIRouter(tags=["admin settings"])

class PlatformSettingsIn(BaseModel):
    commission_percent: int | None = Field(default=None, ge=0, le=50)
    auto_approve_kyc: bool | None = None
    email_alerts: bool | None = None
    payout_hold_hours: int | None = Field(default=None, ge=0, le=720)


@router.get("/settings/platform", dependencies=[Depends(get_current_admin)])
async def get_platform_settings(db: AsyncSession = Depends(get_db)):
    return await load_platform_settings(db)


@router.put("/settings/platform")
async def update_platform_settings(
    body: PlatformSettingsIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    # Platform-wide rules belong to the platform owner, not a city desk.
    if admin_city(admin):
        raise HTTPException(status_code=403, detail="Only an all-cities admin can change platform settings")
    for key, value in body.model_dump(exclude_none=True).items():
        row = (await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))).scalar_one_or_none()
        if row is None:
            db.add(PlatformSetting(key=key, value_json=json.dumps(value)))
        else:
            row.value_json = json.dumps(value)
    await db.commit()
    return await load_platform_settings(db)


class AdminOut(BaseModel):
    id: str
    name: str
    email: str
    city: str
    status: str
    joined_at: datetime


class AdminInviteIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    city: str = ""


class AdminInviteOut(BaseModel):
    admin: AdminOut
    # Shown once to the inviting admin, who passes it on; the new admin
    # signs in with it. There is no outbound email service on this backend.
    temporary_password: str


def _admin_out(u: User) -> AdminOut:
    return AdminOut(
        id=u.id,
        name=u.name,
        email=u.email,
        city=u.admin_city or "",
        status="active" if u.status == ApprovalStatus.approved else u.status.value,
        joined_at=u.joined_at,
    )


@router.get("/admins", response_model=list[AdminOut], dependencies=[Depends(get_current_admin)])
async def list_admins(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(User).where(User.is_admin == True).order_by(User.joined_at.asc()))  # noqa: E712
    return [_admin_out(u) for u in rows.scalars().all()]


@router.post("/admins/invite", response_model=AdminInviteOut, status_code=201)
async def invite_admin(
    body: AdminInviteIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if admin_city(admin):
        raise HTTPException(status_code=403, detail="Only an all-cities admin can add admins")
    email = body.email.lower()
    taken_user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    taken_vendor = (await db.execute(select(Vendor).where(Vendor.email == email))).scalar_one_or_none()
    if taken_user or taken_vendor:
        raise HTTPException(status_code=409, detail="That email already has an AOneGo9 account")
    temp = secrets.token_urlsafe(9)
    new_admin = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(temp),
        status=ApprovalStatus.approved,
        verified=True,
        is_admin=True,
        admin_city=body.city.strip(),
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    return AdminInviteOut(admin=_admin_out(new_admin), temporary_password=temp)
