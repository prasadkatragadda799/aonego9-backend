import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Ads ──────────────────────────────────────────────────────────

class AdCreativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    media: str = "photo"
    headline: str = ""
    sub: str = ""
    image_url: str = ""
    video_url: str = ""
    profile_id: str = ""
    profile_name: str = ""
    profile_cat: str = ""
    website_url: str = ""
    label: str = "Featured"
    city: str = ""
    active: bool = True
    impressions: int = 0
    clicks: int = 0


class AdCreativeCreate(BaseModel):
    media: str = "photo"
    headline: str = ""
    sub: str = ""
    image_url: str = ""
    video_url: str = ""
    profile_id: str = ""
    profile_name: str = ""
    profile_cat: str = ""
    website_url: str = ""
    label: str = "Featured"
    city: str = ""
    active: bool = True


class AdCreativeUpdate(BaseModel):
    media: str | None = None
    headline: str | None = None
    sub: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    profile_id: str | None = None
    profile_name: str | None = None
    profile_cat: str | None = None
    website_url: str | None = None
    label: str | None = None
    city: str | None = None
    active: bool | None = None


class AdCreativeToggle(BaseModel):
    active: bool


# ── Sessions (workshops & webinars) ─────────────────────────────

class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mode: str = "workshop"
    title: str = ""
    host: str = ""
    division: str = "talent"
    city: str = ""
    state: str = ""
    date: str = ""
    time: str = ""
    duration: str = ""
    fee: str = "Free"
    seats: int = 0
    seats_left: int = 0
    blurb: str = ""
    emoji: str = "🎓"
    published: bool = False
    registrations: int = 0


class SessionCreate(BaseModel):
    mode: str = "workshop"
    title: str
    host: str = ""
    division: str = "talent"
    city: str = ""
    state: str = ""
    date: str = ""
    time: str = ""
    duration: str = ""
    fee: str = "Free"
    seats: int = 0
    seats_left: int = 0
    blurb: str = ""
    emoji: str = "🎓"


class SessionUpdate(BaseModel):
    mode: str | None = None
    title: str | None = None
    host: str | None = None
    division: str | None = None
    city: str | None = None
    state: str | None = None
    date: str | None = None
    time: str | None = None
    duration: str | None = None
    fee: str | None = None
    seats: int | None = None
    seats_left: int | None = None
    blurb: str | None = None
    emoji: str | None = None


class SessionToggle(BaseModel):
    published: bool


class SessionRegister(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    email: str
    phone: str = ""
    session_title: str = ""
    mode: str = ""


# ── Partners ─────────────────────────────────────────────────────

class LogoPartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str = ""
    tagline: str = ""
    logo_url: str = ""
    tier: str = "brand"
    division: str = ""
    city: str = ""
    website: str = ""
    published: bool = True


class LogoPartnerCreate(BaseModel):
    name: str
    tagline: str = ""
    logo_url: str = ""
    tier: str = "brand"
    division: str = ""
    city: str = ""
    website: str = ""
    published: bool = True


class LogoPartnerUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    logo_url: str | None = None
    tier: str | None = None
    division: str | None = None
    city: str | None = None
    website: str | None = None
    published: bool | None = None


class PublishToggle(BaseModel):
    published: bool


# ── Team ─────────────────────────────────────────────────────────

class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str = ""
    role: str = ""
    desk: str = "Leadership"
    bio: str = ""
    photo_url: str = ""
    city: str = ""
    published: bool = True


class TeamMemberCreate(BaseModel):
    name: str
    role: str = ""
    desk: str = "Leadership"
    bio: str = ""
    photo_url: str = ""
    city: str = ""
    published: bool = True


class TeamMemberUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    desk: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    city: str | None = None
    published: bool | None = None


# ── Social accounts ──────────────────────────────────────────────

class SocialAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str = ""
    handle: str = ""
    url: str = ""
    followers: int = 0
    connected: bool = False
    owner: str = ""


class SocialAccountCreate(BaseModel):
    platform: str
    handle: str = ""
    url: str = ""
    followers: int = 0
    connected: bool = False
    owner: str = ""


class SocialAccountUpdate(BaseModel):
    platform: str | None = None
    handle: str | None = None
    url: str | None = None
    followers: int | None = None
    connected: bool | None = None
    owner: str | None = None


# ── Leads ─────────────────────────────────────────────────────────

_LEAD_KNOWN_FIELDS = {"kind", "name", "email", "phone", "city", "state", "message"}


class LeadCreate(BaseModel):
    """Accepts every form shape (contact / join / apply_artist / apply_vendor
    / session_register) — anything beyond the known columns is kept as
    free-form detail so a new form field needs no backend change."""

    model_config = ConfigDict(extra="allow")

    kind: str = "contact"
    name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    state: str = ""
    message: str = ""


class LeadOut(BaseModel):
    id: str
    kind: str
    name: str
    email: str
    phone: str
    city: str
    state: str
    message: str
    status: str
    details: dict = Field(default_factory=dict)
    created_at: datetime | None = None


class LeadStatusUpdate(BaseModel):
    status: str


def lead_to_out(row) -> LeadOut:
    try:
        details = json.loads(row.details_json) if row.details_json else {}
    except json.JSONDecodeError:
        details = {}
    return LeadOut(
        id=row.id,
        kind=row.kind,
        name=row.name,
        email=row.email,
        phone=row.phone,
        city=row.city,
        state=row.state,
        message=row.message,
        status=row.status,
        details=details,
        created_at=row.created_at,
    )


def lead_from_create(body: LeadCreate):
    from app.models.directory import Lead

    data = body.model_dump()
    known = {k: data.pop(k) for k in list(_LEAD_KNOWN_FIELDS)}
    return Lead(
        kind=known["kind"] or "contact",
        name=known["name"],
        email=known["email"],
        phone=known["phone"],
        city=known["city"],
        state=known["state"],
        message=known["message"],
        status="new",
        details_json=json.dumps(data),
    )
