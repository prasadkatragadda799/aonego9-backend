from datetime import datetime
from pydantic import BaseModel


class SupportTicketOut(BaseModel):
    id: str
    requester_id: str
    subject: str
    body: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketCreate(BaseModel):
    subject: str
    body: str = ""
    priority: str = "medium"


class SupportTicketUpdate(BaseModel):
    status: str
    priority: str | None = None


class SupportTicketListOut(BaseModel):
    items: list[SupportTicketOut]
    total: int
    open_count: int
