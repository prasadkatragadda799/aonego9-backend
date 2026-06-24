from pydantic import BaseModel


class CmsBannerOut(BaseModel):
    id: str
    title: str
    placement: str
    image_url: str
    link_url: str
    active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CmsBannerCreate(BaseModel):
    title: str
    placement: str = ""
    image_url: str = ""
    link_url: str = ""
    active: bool = True
    sort_order: int = 0


class CmsBannerUpdate(BaseModel):
    title: str | None = None
    placement: str | None = None
    image_url: str | None = None
    link_url: str | None = None
    active: bool | None = None
    sort_order: int | None = None


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    icon: str
    listings: int
    active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    slug: str
    icon: str = ""
    active: bool = True
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    active: bool | None = None
    sort_order: int | None = None
