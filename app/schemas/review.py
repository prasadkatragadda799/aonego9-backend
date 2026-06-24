from datetime import datetime
from pydantic import BaseModel


class ReviewOut(BaseModel):
    id: str
    author_id: str
    vendor_id: str
    booking_id: str | None
    stars: int
    text: str
    reply: str | None
    flagged: bool
    date: datetime

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    vendor_id: str
    booking_id: str | None = None
    stars: int
    text: str


class ReviewReply(BaseModel):
    reply: str


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int
    average_rating: float
