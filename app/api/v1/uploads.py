from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.deps import get_any_authenticated
from app.services.cloudinary_service import is_configured, upload_bytes

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_FOLDERS = {"receipts", "avatars", "portfolio", "cms", "kyc", "misc"}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("misc"),
    _: dict = Depends(get_any_authenticated),
):
    if not is_configured():
        raise HTTPException(status_code=503, detail="Image uploads are not configured yet")
    if folder not in ALLOWED_FOLDERS:
        folder = "misc"

    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        url = upload_bytes(data, folder=f"aonego9/{folder}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Cloudinary upload failed") from exc

    return {"url": url, "folder": f"aonego9/{folder}"}
