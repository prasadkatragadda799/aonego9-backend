from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.directory import Session as SessionModel
from app.models.user import User
from app.schemas.directory import (
    SessionCreate,
    SessionOut,
    SessionRegister,
    SessionToggle,
    SessionUpdate,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SessionModel).where(SessionModel.published == True).order_by(SessionModel.date)
    )
    return result.scalars().all()


@router.get("/admin", response_model=list[SessionOut], dependencies=[Depends(get_current_admin)])
async def admin_list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SessionModel).order_by(SessionModel.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=SessionOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    data = body.model_dump()
    if not data.get("seats_left"):
        data["seats_left"] = data.get("seats", 0)
    row = SessionModel(**data)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.put("/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: str,
    body: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{session_id}", response_model=SessionOut)
async def toggle_session_published(
    session_id: str,
    body: SessionToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    row.published = body.published
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(row)
    await db.commit()


@router.post("/{session_id}/register", status_code=201)
async def register_for_session(session_id: str, body: SessionRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id).with_for_update()
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if not row.published:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.seats > 0 and row.seats_left <= 0:
        raise HTTPException(status_code=409, detail="This session is sold out")
    if row.seats > 0:
        row.seats_left -= 1
    row.registrations += 1
    await db.commit()
    return {"ok": True}
