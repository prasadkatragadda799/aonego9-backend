import cloudinary
import cloudinary.uploader

from app.core.config import settings

MAX_BYTES = 10 * 1024 * 1024


def is_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def _configure() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_bytes(data: bytes, *, folder: str) -> str:
    if not is_configured():
        raise RuntimeError("Cloudinary is not configured")
    if len(data) > MAX_BYTES:
        raise ValueError("File too large (max 10 MB)")
    _configure()
    try:
        result = cloudinary.uploader.upload(data, folder=folder, resource_type="image")
        return result["secure_url"]
    except Exception as exc:
        raise RuntimeError(f"Cloudinary error: {exc}") from exc


def upload_data_uri(data_uri: str, *, folder: str) -> str:
    if not is_configured():
        raise RuntimeError("Cloudinary is not configured")
    _configure()
    result = cloudinary.uploader.upload(data_uri, folder=folder, resource_type="image")
    return result["secure_url"]


def normalize_image_reference(value: str, *, folder: str) -> str:
    """Store Cloudinary URLs in the database; upload inline base64 when configured."""
    if not value:
        return value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("data:") and is_configured():
        return upload_data_uri(value, folder=folder)
    return value
