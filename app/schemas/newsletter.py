from datetime import datetime
from pydantic import BaseModel, EmailStr


class NewsletterIssueOut(BaseModel):
    id: str
    kind: str
    title: str
    excerpt: str
    body: str
    tag: str
    city: str
    emoji: str
    bg: int
    image_url: str
    author: str
    author_email: str
    organisation: str
    credentials_url: str
    date: str
    published_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row) -> "NewsletterIssueOut":
        return cls(
            id=row.id,
            kind=row.kind,
            title=row.title,
            excerpt=row.excerpt,
            body=row.body,
            tag=row.tag,
            city=row.city,
            emoji=row.emoji,
            bg=row.bg,
            image_url=row.image_url,
            author=row.author,
            author_email=row.author_email,
            organisation=row.organisation,
            credentials_url=row.credentials_url,
            date=row.published_at.strftime("%d %b %Y"),
            published_at=row.published_at,
        )


class NewsletterIssueCreate(BaseModel):
    kind: str = "happening"
    title: str
    excerpt: str = ""
    body: str
    tag: str = "Digest"
    city: str = "India"
    emoji: str = "✦"
    bg: int = 0
    image_url: str = ""
    author: str = "AOneGo9 Desk"
    author_email: str = ""
    organisation: str = ""
    credentials_url: str = ""
    date: str | None = None


class NewsletterIssueUpdate(BaseModel):
    kind: str | None = None
    title: str | None = None
    excerpt: str | None = None
    body: str | None = None
    tag: str | None = None
    city: str | None = None
    emoji: str | None = None
    bg: int | None = None
    image_url: str | None = None
    author: str | None = None
    author_email: str | None = None
    organisation: str | None = None
    credentials_url: str | None = None


class NewsletterSubscribeIn(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    city: str = ""


class NewsletterContributeIn(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    city: str = ""
    organisation: str = ""
    headline: str
    story: str = ""
    credentials_url: str = ""


class NewsletterContributionOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    city: str
    organisation: str
    headline: str
    story: str
    credentials_url: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
