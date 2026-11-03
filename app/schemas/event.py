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
    venue: str = ""
    description: str = ""
    image_url: str = ""

    model_config = {"from_attributes": True}


class PlatformEventCreate(BaseModel):
    title: str
    category: str = ""
    city: str = ""
    date: datetime
    status: str = "upcoming"
    on_poster: bool = False
    venue: str = ""
    description: str = ""
    image_url: str = ""


class PlatformEventUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    city: str | None = None
    date: datetime | None = None
    status: str | None = None
    on_poster: bool | None = None
    venue: str | None = None
    description: str | None = None
    image_url: str | None = None


class PosterToggle(BaseModel):
    on_poster: bool


class EventListOut(BaseModel):
    items: list[PlatformEventOut]
    total: int
