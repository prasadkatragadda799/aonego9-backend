from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VendorProfileDetails(Base):
    """Extended marketplace profile content — comp card, scenes, spaces, equipment, etc."""

    __tablename__ = "vendor_profile_details"

    vendor_id: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), primary_key=True)
    experience: Mapped[str] = mapped_column(String(80), default="")
    training: Mapped[str] = mapped_column(String(200), default="")
    languages: Mapped[str] = mapped_column(String(200), default="")
    overview: Mapped[str] = mapped_column(Text, default="")
    # Comp card (models / talent)
    height: Mapped[str] = mapped_column(String(20), default="")
    weight: Mapped[str] = mapped_column(String(20), default="")
    bust: Mapped[str] = mapped_column(String(20), default="")
    chest: Mapped[str] = mapped_column(String(20), default="")
    waist: Mapped[str] = mapped_column(String(20), default="")
    hip: Mapped[str] = mapped_column(String(20), default="")
    shoe: Mapped[str] = mapped_column(String(20), default="")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hair: Mapped[str] = mapped_column(String(40), default="")
    eye: Mapped[str] = mapped_column(String(40), default="")
    skin: Mapped[str] = mapped_column(String(40), default="")
    # JSON blobs — stored as text, parsed in the API layer
    stats_json: Mapped[str] = mapped_column(Text, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    services_json: Mapped[str] = mapped_column(Text, default="[]")
    amenities_json: Mapped[str] = mapped_column(Text, default="[]")
    availability_json: Mapped[str] = mapped_column(Text, default="[]")
    scene_data_json: Mapped[str] = mapped_column(Text, default="[]")
    spaces_json: Mapped[str] = mapped_column(Text, default="[]")
    equipment_json: Mapped[str] = mapped_column(Text, default="[]")
    reels_json: Mapped[str] = mapped_column(Text, default="[]")

    vendor = relationship("Vendor", back_populates="profile_details")
