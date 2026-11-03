from datetime import datetime
from pydantic import BaseModel, Field


class BookingOut(BaseModel):
    id: str
    client_id: str
    client_name: str = ""
    vendor_id: str
    vendor_name: str = ""
    service: str
    package_id: str | None
    date: datetime
    amount: float
    advance_paid: float
    balance_due: float
    status: str
    source: str
    inquiry_ref: str | None
    location: str
    notes: str
    created_at: datetime
    # The client's contact, so the vendor can call/email about the job.
    client_email: str = ""
    client_phone: str = ""

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_balance(cls, obj):
        data = {
            **{c: getattr(obj, c) for c in cls.model_fields},
            "balance_due": max(0.0, obj.amount - obj.advance_paid),
            "status": obj.status.value,
            "source": obj.source.value,
        }
        return cls(**data)


class BookingCreate(BaseModel):
    vendor_id: str
    service: str
    package_id: str | None = None
    date: datetime
    amount: float
    location: str = ""
    notes: str = ""
    source: str = "direct"
    inquiry_ref: str | None = None


class BookingStatusUpdate(BaseModel):
    status: str


class BookingQuote(BaseModel):
    """The vendor's price for an inquiry booking (inquiries arrive at 0)."""

    amount: float = Field(gt=0, le=100_000_000)


class AdvancePayment(BaseModel):
    booking_id: str
    inquiry_ref: str = ""
    amount: float = 5000.0
    method: str = "UPI"
    receipt_image: str = ""


class AdvanceRequestOut(BaseModel):
    id: str
    booking_id: str
    user_id: str
    client_name: str = ""
    vendor_name: str = ""
    inquiry_ref: str | None = None
    amount: float
    receipt_image: str
    status: str
    admin_note: str
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdvanceReview(BaseModel):
    admin_note: str = ""


class BookingListOut(BaseModel):
    items: list[BookingOut]
    total: int
    page: int
    page_size: int
