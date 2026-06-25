from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import ApprovalStatus, User, UserRole
from app.models.vendor import Vendor
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterUserRequest,
    RegisterVendorRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/user", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(body: RegisterUserRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        city=body.city,
        password_hash=hash_password(body.password),
        role=UserRole(body.role) if body.role in [r.value for r in UserRole] else UserRole.client,
        status=ApprovalStatus.approved,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user.id, "user"),
        refresh_token=create_refresh_token(user.id, "user"),
        role="user",
    )


@router.post("/register/vendor", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_vendor(body: RegisterVendorRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Vendor).where(Vendor.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    vendor = Vendor(
        name=body.name,
        company=body.company,
        email=body.email,
        phone=body.phone,
        city=body.city,
        category=body.category,
        password_hash=hash_password(body.password),
        status=ApprovalStatus.approved,  # auto-approve for demo; admin can suspend later
    )
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return TokenResponse(
        access_token=create_access_token(vendor.id, "vendor"),
        refresh_token=create_refresh_token(vendor.id, "vendor"),
        role="vendor",
    )


@router.post("/login/user", response_model=TokenResponse)
async def login_user(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.id, "user"),
        refresh_token=create_refresh_token(user.id, "user"),
        role="user",
    )


@router.post("/login/vendor", response_model=TokenResponse)
async def login_vendor(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.email == body.email))
    vendor = result.scalar_one_or_none()
    if not vendor or not verify_password(body.password, vendor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(vendor.id, "vendor"),
        refresh_token=create_refresh_token(vendor.id, "vendor"),
        role="vendor",
    )


@router.post("/login/admin", response_model=TokenResponse)
async def login_admin(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_admin == True))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(admin.id, "admin"),
        refresh_token=create_refresh_token(admin.id, "admin"),
        role="admin",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        sub = payload["sub"]
        role = payload["role"]
        return TokenResponse(
            access_token=create_access_token(sub, role),
            refresh_token=create_refresh_token(sub, role),
            role=role,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
