from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TicketPriority = Literal["low", "medium", "high"]
TicketStatus = Literal["open", "pending", "resolved"]


class SupportTicketOut(BaseModel):
    id: str
    requester_id: str
    subject: str
    body: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    requester_name: str = ""
    requester_email: str = ""

    model_config = {"from_attributes": True}


class SupportTicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field("", max_length=5000)
    priority: TicketPriority = "medium"


class SupportTicketUpdate(BaseModel):
    status: TicketStatus
    priority: TicketPriority | None = None


class SupportTicketListOut(BaseModel):
    items: list[SupportTicketOut]
    total: int
    open_count: int
