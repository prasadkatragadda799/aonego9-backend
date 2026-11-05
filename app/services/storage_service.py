"""Image storage in Postgres — no third-party services (works on Render free tier)."""

from __future__ import annotations

import base64
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services import database_storage

MAX_BYTES = 10 * 1024 * 1024


def effective_backend() -> str:
    raw = (settings.STORAGE_BACKEND or "auto").strip().lower()
    if raw not in ("", "auto"):
        return raw
    if cloudinary_service.is_configured():
        return "cloudinary"
    if s3_storage.is_configured():
        return "s3"
    if database_storage.is_configured():
        return "database"
    return "none"


def is_configured() -> bool:
    return database_storage.is_configured()


def media_public_url(media_id: str) -> str:
    base = settings.public_api_base_url.rstrip("/")
    return f"{base}/api/v1/media/{media_id}"


async def upload_bytes_async(
    db: AsyncSession,
    data: bytes,
    *,
    folder: str,
    content_type: str = "image/jpeg",
) -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("File too large (max 10 MB)")
    if not settings.public_api_base_url:
        raise RuntimeError(
            "Set PUBLIC_API_BASE_URL to your backend URL (e.g. https://your-app.onrender.com)"
        )
    media_id = str(uuid.uuid4())
    await database_storage.save_blob(
        db,
        media_id=media_id,
        data=data,
        folder=folder,
        content_type=content_type,
    )
    return media_public_url(media_id)


async def normalize_image_reference(db: AsyncSession, value: str, *, folder: str) -> str:
    """Keep HTTPS URLs; store inline base64 / data-URIs as media rows."""
    if not value:
        return value
    trimmed = value.strip()
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        return trimmed
    if trimmed.startswith("/api/v1/media/"):
        base = settings.public_api_base_url.rstrip("/")
        return f"{base}{trimmed}" if base else trimmed

    data: bytes | None = None
    content_type = "image/jpeg"
    if trimmed.startswith("data:"):
        header, _, payload = trimmed.partition(",")
        if ";" in header and ":" in header:
            content_type = header.split(":", 1)[1].split(";")[0].strip() or content_type
        try:
            data = base64.b64decode(payload, validate=True)
        except Exception:
            return trimmed
    elif len(trimmed) > 200:
        try:
            data = base64.b64decode(trimmed, validate=True)
        except Exception:
            data = None

    if not data:
        return trimmed

    if not is_configured():
        return trimmed

    return await upload_bytes_async(db, data, folder=folder, content_type=content_type)
