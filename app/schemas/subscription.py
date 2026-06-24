from datetime import datetime
from pydantic import BaseModel


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    price: float
    period: str
    features: list[str]
    recommended: bool

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
        )


class VendorSubscriptionOut(BaseModel):
    plan_id: str
    plan_name: str
    price: float
    status: str
    renews_on: datetime

    model_config = {"from_attributes": True}


class SubscribeRequest(BaseModel):
    plan_id: str
    payment_method: str = "Card"


class BillingEntryOut(BaseModel):
    id: str
    date: datetime
    description: str
    amount: float
    status: str

    model_config = {"from_attributes": True}
