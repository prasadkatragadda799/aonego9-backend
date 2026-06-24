from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.models.user import ApprovalStatus, User
from app.schemas.user import UserListOut, UserOut, UserStatusUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("", response_model=UserListOut, dependencies=[Depends(get_current_admin)])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(User)
    if status:
        q = q.where(User.status == ApprovalStatus(status))
    if role:
        from app.models.user import UserRole
        q = q.where(User.role == UserRole(role))
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()
    return UserListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(get_current_admin)])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}/status", response_model=UserOut)
async def update_user_status(
    user_id: str,
    body: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = ApprovalStatus(body.status)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/verify", response_model=UserOut)
async def verify_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.verified = True
    await db.commit()
    await db.refresh(user)
    return user
