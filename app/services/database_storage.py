from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.media_file import MediaFile


def is_configured() -> bool:
    # Postgres/SQLite both work; production needs a public API base for absolute image URLs.
    if settings.is_production and not settings.PUBLIC_API_BASE_URL.strip():
        return False
    return True


async def save_blob(
    db: AsyncSession,
    *,
    media_id: str,
    data: bytes,
    folder: str,
    content_type: str,
) -> MediaFile:
    row = MediaFile(id=media_id, folder=folder, content_type=content_type, data=data)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_blob(db: AsyncSession, media_id: str) -> MediaFile | None:
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    return result.scalar_one_or_none()
