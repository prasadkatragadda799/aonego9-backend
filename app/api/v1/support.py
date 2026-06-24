from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.models.subscription import SupportTicket
from app.models.user import User
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketListOut,
    SupportTicketOut,
    SupportTicketUpdate,
)

router = APIRouter(prefix="/support", tags=["support"])


@router.post("", response_model=SupportTicketOut, status_code=201)
async def create_ticket(
    body: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = SupportTicket(
        requester_id=current_user.id,
        subject=body.subject,
        body=body.body,
        priority=body.priority,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/admin", response_model=SupportTicketListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_tickets(
    status: str | None = None,
    priority: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(SupportTicket)
    if status:
        q = q.where(SupportTicket.status == status)
    if priority:
        q = q.where(SupportTicket.priority == priority)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    open_count = (
        await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status == "open"))
    ).scalar_one()
    paginated = await db.execute(q.order_by(SupportTicket.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return SupportTicketListOut(items=paginated.scalars().all(), total=total, open_count=open_count)


@router.get("/admin/{ticket_id}", response_model=SupportTicketOut, dependencies=[Depends(get_current_admin)])
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/admin/{ticket_id}", response_model=SupportTicketOut)
async def update_ticket(
    ticket_id: str,
    body: SupportTicketUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = body.status
    if body.priority:
        ticket.priority = body.priority
    await db.commit()
    await db.refresh(ticket)
    return ticket
