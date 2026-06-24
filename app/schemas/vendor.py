from datetime import datetime
from pydantic import BaseModel, EmailStr


class VendorOut(BaseModel):
    id: str
    name: str
    company: str
    email: EmailStr
    phone: str
    city: str
    category: str
    bio: str
    avatar_url: str
    status: str
    kyc_verified: bool
    rating: float
    total_bookings: int
    total_earnings: float
    plan: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class VendorPublicOut(BaseModel):
    """Reduced profile for the public browse/listing view."""
    id: str
    name: str
    company: str
    city: str
    category: str
    bio: str
    avatar_url: str
    rating: float
    total_bookings: int
    plan: str

    model_config = {"from_attributes": True}


class VendorUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    city: str | None = None
    category: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class VendorStatusUpdate(BaseModel):
    status: str


class VendorKycUpdate(BaseModel):
    kyc_verified: bool


class ServicePackageOut(BaseModel):
    id: str
    vendor_id: str
    title: str
    category: str
    price: float
    unit: str
    description: str
    active: bool
    bookings_count: int

    model_config = {"from_attributes": True}


class ServicePackageCreate(BaseModel):
    title: str
    category: str = ""
    price: float
    unit: str = ""
    description: str = ""
    active: bool = True


class ServicePackageUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    price: float | None = None
    unit: str | None = None
    description: str | None = None
    active: bool | None = None


class TalentMemberOut(BaseModel):
    id: str
    vendor_id: str
    name: str
    role: str
    city: str
    day_rate: float
    rating: float
    available: bool
    shoots: int
    avatar_url: str

    model_config = {"from_attributes": True}


class TalentMemberCreate(BaseModel):
    name: str
    role: str = ""
    city: str = ""
    day_rate: float = 0.0
    rating: float = 0.0
    available: bool = True
    shoots: int = 0
    avatar_url: str = ""


class TalentMemberUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    city: str | None = None
    day_rate: float | None = None
    available: bool | None = None


class VendorListOut(BaseModel):
    items: list[VendorOut]
    total: int
    page: int
    page_size: int
