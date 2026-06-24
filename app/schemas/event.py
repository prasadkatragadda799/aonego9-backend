from datetime import datetime
from pydantic import BaseModel


class PlatformEventOut(BaseModel):
    id: str
    title: str
    category: str
    city: str
    date: datetime
    status: str
    on_poster: bool
    registrations: int

    model_config = {"from_attributes": True}


class PlatformEventCreate(BaseModel):
    title: str
    category: str = ""
    city: str = ""
    date: datetime
    status: str = "upcoming"
    on_poster: bool = False


class PlatformEventUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    city: str | None = None
    date: datetime | None = None
    status: str | None = None
    on_poster: bool | None = None


class PosterToggle(BaseModel):
    on_poster: bool


class EventListOut(BaseModel):
    items: list[PlatformEventOut]
    total: int
