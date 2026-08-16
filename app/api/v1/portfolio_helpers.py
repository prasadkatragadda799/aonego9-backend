from app.models.vendor import PortfolioItem
from app.utils.url_lists import dump_url_list, parse_url_list, validate_url_list, MAX_PORTFOLIO_IMAGES


def portfolio_images(item: PortfolioItem) -> list[str]:
    images = parse_url_list(item.images_json)
    if not images and item.image_url:
        return [item.image_url]
    return images


def apply_portfolio_images(
    item: PortfolioItem,
    *,
    images: list[str] | None = None,
    image_url: str | None = None,
) -> None:
    if images is not None:
        urls = validate_url_list(images, max_count=MAX_PORTFOLIO_IMAGES, field_name="images")
        item.images_json = dump_url_list(urls, max_count=MAX_PORTFOLIO_IMAGES)
        item.image_url = urls[0] if urls else ""
        return
    if image_url is not None:
        item.image_url = image_url
        if image_url.strip():
            item.images_json = dump_url_list([image_url.strip()], max_count=MAX_PORTFOLIO_IMAGES)
        else:
            item.images_json = "[]"


def portfolio_payload_to_item_fields(body: dict) -> dict:
    """Split API payload into SQLAlchemy scalar fields + image side effects."""
    data = dict(body)
    images = data.pop("images", None)
    image_url = data.pop("image_url", None)
    return data, images, image_url
