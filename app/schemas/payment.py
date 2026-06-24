from datetime import datetime
from pydantic import BaseModel


class PaymentTxnOut(BaseModel):
    id: str
    booking_id: str | None
    party: str
    type: str
    amount: float
    status: str
    method: str
    date: datetime

    model_config = {"from_attributes": True}


class EarningTxnOut(BaseModel):
    id: str
    vendor_id: str
    booking_id: str | None
    source: str
    type: str
    amount: float
    status: str
    date: datetime

    model_config = {"from_attributes": True}


class PayoutRequest(BaseModel):
    vendor_id: str
    amount: float
    method: str = "Bank Transfer"


class PaymentListOut(BaseModel):
    items: list[PaymentTxnOut]
    total: int
    page: int
    page_size: int


class EarningsListOut(BaseModel):
    items: list[EarningTxnOut]
    total_earned: float
    total_pending: float
    total_paid_out: float
    page: int
    page_size: int
