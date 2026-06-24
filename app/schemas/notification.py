from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    vendor_id: str
    title: str
    body: str
    kind: str
    unread: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int
