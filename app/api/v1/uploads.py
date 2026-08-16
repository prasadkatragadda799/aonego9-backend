from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.core.deps import get_any_authenticated
from app.services.cloudinary_service import is_configured, upload_bytes

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_FOLDERS = {"receipts", "avatars", "portfolio", "cms", "kyc", "misc"}


class ImageBase64Upload(BaseModel):
    """JSON/base64 upload — more reliable for Flutter web than multipart."""

    data: str = Field(..., description="Raw base64 or data-URI")
    filename: str = "photo.jpg"
    folder: str = "misc"
    content_type: str = "image/jpeg"


def _upload_to_cloudinary(data: bytes, folder: str) -> dict:
    if not is_configured():
        raise HTTPException(status_code=503, detail="Image uploads are not configured yet")
    if folder not in ALLOWED_FOLDERS:
        folder = "misc"
    try:
        url = upload_bytes(data, folder=f"aonego9/{folder}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {exc}") from exc
    return {"url": url, "folder": f"aonego9/{folder}"}


@router.post("/image-base64")
async def upload_image_base64(
    body: ImageBase64Upload,
    _: dict = Depends(get_any_authenticated),
):
    import base64

    raw = body.data.strip()
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image data") from exc
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    return _upload_to_cloudinary(data, body.folder)


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("misc"),
    _: dict = Depends(get_any_authenticated),
):
    content_type = (file.content_type or "").lower()
    if content_type and not (
        content_type.startswith("image/")
        or content_type in {"application/octet-stream", "binary/octet-stream"}
    ):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    return _upload_to_cloudinary(data, folder)
