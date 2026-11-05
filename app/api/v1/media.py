from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import database_storage

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{media_id}")
async def get_media(media_id: str, db: AsyncSession = Depends(get_db)):
    row = await database_storage.get_blob(db, media_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(
        content=row.data,
        media_type=row.content_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
