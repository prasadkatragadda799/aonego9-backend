from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_any_authenticated
from app.services import storage_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_FOLDERS = {"receipts", "avatars", "portfolio", "cms", "kyc", "misc"}


class ImageBase64Upload(BaseModel):
    """JSON/base64 upload — more reliable for Flutter web than multipart."""

    data: str = Field(..., description="Raw base64 or data-URI")
    filename: str = "photo.jpg"
    folder: str = "misc"
    content_type: str = "image/jpeg"


async def _upload(data: bytes, folder: str, content_type: str, db: AsyncSession) -> dict:
    if not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Set PUBLIC_API_BASE_URL to your backend URL (e.g. https://your-app.onrender.com).",
        )
    if folder not in ALLOWED_FOLDERS:
        folder = "misc"
    target_folder = f"aonego9/{folder}"
    try:
        url = await storage_service.upload_bytes_async(
            db, data, folder=target_folder, content_type=content_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upload failed: {exc}") from exc
    return {"url": url, "folder": target_folder}


@router.post("/image-base64")
async def upload_image_base64(
    body: ImageBase64Upload,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_any_authenticated),
):
    import base64

    raw = body.data.strip()
    content_type = body.content_type or "image/jpeg"
    if raw.startswith("data:") and "," in raw:
        header, raw = raw.split(",", 1)
        if ";" in header and ":" in header:
            content_type = header.split(":", 1)[1].split(";")[0].strip() or content_type
    try:
        data = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image data") from exc
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return await _upload(data, body.folder, content_type, db)


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("misc"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_any_authenticated),
):
    content_type = (file.content_type or "image/jpeg").lower()
    if content_type and not (
        content_type.startswith("image/")
        or content_type in {"application/octet-stream", "binary/octet-stream"}
    ):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    return await _upload(data, folder, content_type if content_type.startswith("image/") else "image/jpeg", db)
