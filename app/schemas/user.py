from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    city: str
    role: str
    status: str
    verified: bool
    rating: float
    jobs_done: int
    avatar_url: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    avatar_url: str | None = None


class UserStatusUpdate(BaseModel):
    status: str


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
