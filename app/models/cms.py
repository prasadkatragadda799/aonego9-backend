import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CmsBanner(Base):
    __tablename__ = "cms_banners"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"C-{uuid.uuid4().hex[:8].upper()}")
    title: Mapped[str] = mapped_column(String(200))
    placement: Mapped[str] = mapped_column(String(100), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    link_url: Mapped[str] = mapped_column(String(500), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"CAT-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    icon: Mapped[str] = mapped_column(String(10), default="")
    listings: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
