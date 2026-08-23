from app.models.vendor import PortfolioItem, Vendor
from app.schemas.vendor import PortfolioItemOut, VendorOut, VendorPublicOut
from app.utils.url_lists import parse_url_list


def vendor_to_out(vendor: Vendor) -> VendorOut:
    return VendorOut(
        id=vendor.id,
        name=vendor.name,
        company=vendor.company,
        email=vendor.email,
        phone=vendor.phone,
        city=vendor.city,
        category=vendor.category,
        bio=vendor.bio,
        avatar_url=vendor.avatar_url,
        gallery_urls=parse_url_list(vendor.gallery_urls_json),
        status=vendor.status.value if hasattr(vendor.status, "value") else str(vendor.status),
        kyc_verified=vendor.kyc_verified,
        rating=vendor.rating,
        total_bookings=vendor.total_bookings,
        total_earnings=vendor.total_earnings,
        plan=vendor.plan,
        joined_at=vendor.joined_at,
        phone_verified=vendor.phone_verified,
        last_login_at=vendor.last_login_at,
    )


def vendor_to_public_out(vendor: Vendor) -> VendorPublicOut:
    return VendorPublicOut(
        id=vendor.id,
        name=vendor.name,
        company=vendor.company,
        city=vendor.city,
        category=vendor.category,
        bio=vendor.bio,
        avatar_url=vendor.avatar_url,
        gallery_urls=parse_url_list(vendor.gallery_urls_json),
        kyc_verified=vendor.kyc_verified,
        rating=vendor.rating,
        total_bookings=vendor.total_bookings,
        plan=vendor.plan,
    )


def portfolio_item_to_out(item: PortfolioItem) -> PortfolioItemOut:
    images = parse_url_list(item.images_json)
    if not images and item.image_url:
        images = [item.image_url]
    cover = images[0] if images else item.image_url
    return PortfolioItemOut(
        id=item.id,
        vendor_id=item.vendor_id,
        headline=item.headline,
        description=item.description,
        tag=item.tag,
        emoji=item.emoji,
        bg=item.bg,
        image_url=cover,
        images=images,
        featured=item.featured,
        type=item.type,
        sort_order=item.sort_order,
    )
