import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsletterIssue(Base):
    __tablename__ = "newsletter_issues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"NL-{uuid.uuid4().hex[:8].upper()}")
    kind: Mapped[str] = mapped_column(String(20), default="happening")  # happening | trend
    title: Mapped[str] = mapped_column(String(300))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    tag: Mapped[str] = mapped_column(String(80), default="Digest")
    city: Mapped[str] = mapped_column(String(100), default="India")
    emoji: Mapped[str] = mapped_column(String(10), default="✦")
    bg: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    author: Mapped[str] = mapped_column(String(120), default="AOneGo9 Desk")
    author_email: Mapped[str] = mapped_column(String(255), default="")
    organisation: Mapped[str] = mapped_column(String(200), default="")
    credentials_url: Mapped[str] = mapped_column(String(500), default="")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class NewsletterContribution(Base):
    """User/vendor story pitches awaiting editorial review."""
    __tablename__ = "newsletter_contributions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"NC-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(30), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    organisation: Mapped[str] = mapped_column(String(200), default="")
    headline: Mapped[str] = mapped_column(String(300))
    story: Mapped[str] = mapped_column(Text, default="")
    credentials_url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | published | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
