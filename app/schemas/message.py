from datetime import datetime
from pydantic import BaseModel


class ChatMessageOut(BaseModel):
    id: str
    thread_id: str
    text: str
    from_vendor: bool
    sent_at: datetime

    model_config = {"from_attributes": True}


class ChatThreadOut(BaseModel):
    id: str
    vendor_id: str
    participant_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int

    model_config = {"from_attributes": True}


class ChatThreadDetailOut(ChatThreadOut):
    messages: list[ChatMessageOut]


class SendMessageRequest(BaseModel):
    text: str
