from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.url_lists import MAX_GALLERY_IMAGES, MAX_PORTFOLIO_IMAGES, validate_url_list


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
    gallery_urls: list[str] = Field(default_factory=list)
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
    gallery_urls: list[str] = Field(default_factory=list)
    kyc_verified: bool
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
    gallery_urls: list[str] | None = None

    @field_validator("gallery_urls")
    @classmethod
    def _validate_gallery(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return validate_url_list(v, max_count=MAX_GALLERY_IMAGES, field_name="gallery_urls")


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


class PortfolioItemOut(BaseModel):
    id: str
    vendor_id: str
    headline: str
    description: str
    tag: str
    emoji: str
    bg: int
    image_url: str
    images: list[str] = Field(default_factory=list)
    featured: bool
    type: str
    sort_order: int

    model_config = {"from_attributes": True}


class PortfolioItemCreate(BaseModel):
    headline: str
    description: str = ""
    tag: str = ""
    emoji: str = "🖼️"
    bg: int = 0
    image_url: str = ""
    images: list[str] = Field(default_factory=list)
    featured: bool = False
    type: str = ""
    sort_order: int = 0

    @field_validator("images")
    @classmethod
    def _validate_images(cls, v: list[str]) -> list[str]:
        return validate_url_list(v, max_count=MAX_PORTFOLIO_IMAGES, field_name="images")


class PortfolioItemUpdate(BaseModel):
    headline: str | None = None
    description: str | None = None
    tag: str | None = None
    emoji: str | None = None
    bg: int | None = None
    image_url: str | None = None
    images: list[str] | None = None
    featured: bool | None = None
    type: str | None = None
    sort_order: int | None = None

    @field_validator("images")
    @classmethod
    def _validate_images(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return validate_url_list(v, max_count=MAX_PORTFOLIO_IMAGES, field_name="images")


class VendorListOut(BaseModel):
    items: list[VendorOut]
    total: int
    page: int
    page_size: int
