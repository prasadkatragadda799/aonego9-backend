from datetime import datetime
from pydantic import BaseModel, Field


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    price: float
    period: str
    features: list[str]
    recommended: bool
    audience: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        features = [f.strip() for f in obj.features.split("\n") if f.strip()] if obj.features else []
        return cls(
            id=obj.id,
            name=obj.name,
            price=obj.price,
            period=obj.period,
            features=features,
            recommended=obj.recommended,
            audience=obj.audience,
        )


class PlanCreateUpdate(BaseModel):
    name: str
    price: float = 0.0
    period: str = "per month"
    features: list[str] = []
    recommended: bool = False
    audience: str = "both"  # "vendor" | "user" | "both"


class VendorSubscriptionOut(BaseModel):
    plan_id: str
    plan_name: str
    price: float
    status: str
    renews_on: datetime

    model_config = {"from_attributes": True}


class ClientSubscriptionOut(BaseModel):
    plan_id: str
    plan_name: str
    price: float
    status: str
    renews_on: datetime

    model_config = {"from_attributes": True}


class BillingEntryOut(BaseModel):
    id: str
    date: datetime
    description: str
    amount: float
    status: str

    model_config = {"from_attributes": True}


class SubscriptionRequestIn(BaseModel):
    plan_id: str
    receipt_image: str  # Cloudinary HTTPS URL (legacy base64 data URIs are auto-uploaded when configured)


class SubscriptionRequestOut(BaseModel):
    id: str
    requester_type: str
    vendor_id: str | None
    user_id: str | None
    plan_id: str
    plan_name: str
    amount: float
    receipt_image: str
    status: str
    admin_note: str
    created_at: datetime
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class SubscriptionReviewIn(BaseModel):
    admin_note: str = ""


class PaymentSettingsOut(BaseModel):
    upi_id: str
    payee_name: str
    advance_amount: float = 5000.0

    model_config = {"from_attributes": True}


class PaymentSettingsIn(BaseModel):
    upi_id: str
    payee_name: str = "AOneGo9"
    advance_amount: float = Field(default=5000.0, gt=0)


class AdminAssignSubscriptionIn(BaseModel):
    plan_id: str
