import json

MAX_GALLERY_IMAGES = 8
MAX_PORTFOLIO_IMAGES = 8


def parse_url_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    return [str(u).strip() for u in data if str(u).strip()]


def dump_url_list(urls: list[str] | None, *, max_count: int) -> str:
    cleaned = [u.strip() for u in (urls or []) if u and u.strip()][:max_count]
    return json.dumps(cleaned)


def validate_url_list(urls: list[str] | None, *, max_count: int, field_name: str) -> list[str]:
    cleaned = [u.strip() for u in (urls or []) if u and u.strip()]
    if len(cleaned) > max_count:
        raise ValueError(f"{field_name} supports at most {max_count} images")
    return cleaned
