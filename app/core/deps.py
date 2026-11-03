from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import ApprovalStatus, User
from app.models.vendor import Vendor

bearer_scheme = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


async def _get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Use an access token, not a refresh token")
    return payload


async def get_current_user(
    payload: dict = Depends(_get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    if payload.get("role") != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User access only")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status != ApprovalStatus.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    return user


async def get_current_vendor(
    payload: dict = Depends(_get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> Vendor:
    if payload.get("role") != "vendor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor access only")
    result = await db.execute(select(Vendor).where(Vendor.id == payload["sub"]))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Vendor not found")
    # A vendor uses their own console whatever their approval status: a new
    # vendor has to build the profile and portfolio the desk approves them on.
    # Marketplace visibility is gated separately — every public listing,
    # profile and inquiry route filters on ApprovalStatus.approved.
    return vendor


async def get_current_admin(
    payload: dict = Depends(_get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access only")
    result = await db.execute(select(User).where(User.id == payload["sub"], User.is_admin == True))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    return admin


async def get_optional_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> dict | None:
    """Token payload when a valid access token is sent, otherwise None —
    for public routes that trust the caller's identity when it is known."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None
    return None if payload.get("type") == "refresh" else payload


async def get_any_authenticated(
    payload: dict = Depends(_get_token_payload),
) -> dict:
    """Returns the raw token payload — useful for endpoints accessible to any role."""
    return payload
