"""Directory content the superadmin desk curates for the marketplace to
render: ad creatives, workshops & webinars, academic + brand partners, the
team roster, social accounts and inbound leads from the contact / join /
apply forms."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdCreative(Base):
    __tablename__ = "ad_creatives"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"AD-{uuid.uuid4().hex[:8].upper()}")
    media: Mapped[str] = mapped_column(String(10), default="photo")  # video | photo
    headline: Mapped[str] = mapped_column(String(300), default="")
    sub: Mapped[str] = mapped_column(String(500), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    profile_id: Mapped[str] = mapped_column(String, default="")
    profile_name: Mapped[str] = mapped_column(String(200), default="")
    profile_cat: Mapped[str] = mapped_column(String(80), default="")
    website_url: Mapped[str] = mapped_column(String(500), default="")
    label: Mapped[str] = mapped_column(String(80), default="Featured")
    city: Mapped[str] = mapped_column(String(100), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Session(Base):
    """A workshop (in person) or webinar (online)."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"SS-{uuid.uuid4().hex[:8].upper()}")
    mode: Mapped[str] = mapped_column(String(10), default="workshop")  # workshop | webinar
    title: Mapped[str] = mapped_column(String(300), default="")
    host: Mapped[str] = mapped_column(String(200), default="")
    division: Mapped[str] = mapped_column(String(40), default="talent")
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(100), default="")
    date: Mapped[str] = mapped_column(String(40), default="")
    time: Mapped[str] = mapped_column(String(40), default="")
    duration: Mapped[str] = mapped_column(String(40), default="")
    fee: Mapped[str] = mapped_column(String(40), default="Free")
    seats: Mapped[int] = mapped_column(Integer, default=0)
    seats_left: Mapped[int] = mapped_column(Integer, default=0)
    blurb: Mapped[str] = mapped_column(Text, default="")
    emoji: Mapped[str] = mapped_column(String(10), default="🎓")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    registrations: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LogoPartner(Base):
    __tablename__ = "logo_partners"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"PT-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(200), default="")
    tagline: Mapped[str] = mapped_column(String(500), default="")
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    tier: Mapped[str] = mapped_column(String(20), default="brand")  # academic | brand | institutional
    division: Mapped[str] = mapped_column(String(100), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    website: Mapped[str] = mapped_column(String(500), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"TM-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(200), default="")
    desk: Mapped[str] = mapped_column(String(100), default="Leadership")
    bio: Mapped[str] = mapped_column(Text, default="")
    photo_url: Mapped[str] = mapped_column(String(500), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"SA-{uuid.uuid4().hex[:8].upper()}")
    platform: Mapped[str] = mapped_column(String(40), default="")
    handle: Mapped[str] = mapped_column(String(100), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    followers: Mapped[int] = mapped_column(Integer, default=0)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    owner: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Lead(Base):
    """One submission from the contact / join us / apply forms, or a session
    registration that fell back after /sessions/{id}/register failed."""

    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"LD-{uuid.uuid4().hex[:8].upper()}")
    kind: Mapped[str] = mapped_column(String(30), default="contact")
    name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(100), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="new")  # new | in_progress | closed
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
