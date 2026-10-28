from datetime import datetime
from pydantic import BaseModel, Field


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
    stars: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=5000)


class ReviewReply(BaseModel):
    reply: str


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int
    average_rating: float


class ReviewPublicOut(BaseModel):
    id: str
    author: str
    stars: int
    text: str
    reply: str | None
    date: datetime


class ReviewPublicListOut(BaseModel):
    items: list[ReviewPublicOut]
    total: int
    average_rating: float
