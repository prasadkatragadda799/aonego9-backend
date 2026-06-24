from pydantic import BaseModel


class BrowseCategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    icon: str
    count: int
    filters: list[str]

    model_config = {"from_attributes": True}


class InquiryCreate(BaseModel):
    vendor_id: str
    category: str
    name: str
    email: str
    phone: str
    date: str
    message: str = ""
    urgent: bool = False
    inquiry_ref: str


class InquiryOut(BaseModel):
    inquiry_ref: str
    vendor_id: str
    status: str = "submitted"
    message: str = "Your inquiry has been sent to the vendor."


class TickerItem(BaseModel):
    id: str
    title: str
    category: str
    city: str
    date: str
    on_poster: bool
