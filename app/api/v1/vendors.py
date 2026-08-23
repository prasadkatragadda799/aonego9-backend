from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_vendor
from app.models.user import ApprovalStatus, User
from app.models.vendor import ServicePackage, PortfolioItem, TalentMember, Vendor
from app.api.v1.portfolio_helpers import apply_portfolio_images
from app.api.v1.vendor_profile_helpers import get_approved_vendor, get_or_create_details
from app.schemas.vendor_serializers import portfolio_item_to_out, vendor_to_out, vendor_to_public_out
from app.utils.url_lists import dump_url_list, validate_url_list, MAX_GALLERY_IMAGES
from app.schemas.vendor_profile import VendorProfileDetailsOut, VendorProfileDetailsUpdate, apply_update, details_to_out
from app.schemas.vendor import (
    PortfolioItemCreate,
    PortfolioItemOut,
    PortfolioItemUpdate,
    ServicePackageCreate,
    ServicePackageOut,
    ServicePackageUpdate,
    TalentMemberCreate,
    TalentMemberOut,
    TalentMemberUpdate,
    VendorKycUpdate,
    VendorListOut,
    VendorOut,
    VendorPublicOut,
    VendorStatusUpdate,
    VendorUpdate,
)

router = APIRouter(prefix="/vendors", tags=["vendors"])


# ── Public browse ────────────────────────────────────────────

@router.get("", response_model=list[VendorPublicOut])
async def list_vendors_public(
    category: str | None = None,
    city: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Vendor).where(Vendor.status == ApprovalStatus.approved)
    if category:
        q = q.where(Vendor.category == category)
    if city:
        q = q.where(Vendor.city == city)
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return [vendor_to_public_out(v) for v in result.scalars().all()]


@router.get("/public/{vendor_id}", response_model=VendorPublicOut)
async def get_vendor_public(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.status == ApprovalStatus.approved))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor_to_public_out(vendor)


@router.get("/public/{vendor_id}/packages", response_model=list[ServicePackageOut])
async def get_vendor_packages_public(vendor_id: str, db: AsyncSession = Depends(get_db)):
    """Active packages for a vendor — shown on the vendor's public profile in the user app."""
    result = await db.execute(
        select(ServicePackage).where(
            ServicePackage.vendor_id == vendor_id,
            ServicePackage.active == True,
        )
    )
    return result.scalars().all()


@router.get("/public/{vendor_id}/portfolio", response_model=list[PortfolioItemOut])
async def get_vendor_portfolio_public(vendor_id: str, db: AsyncSession = Depends(get_db)):
    """Portfolio works for an approved vendor — shown on the public profile."""
    vendor_result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id, Vendor.status == ApprovalStatus.approved)
    )
    if not vendor_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vendor not found")
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.vendor_id == vendor_id)
        .order_by(PortfolioItem.featured.desc(), PortfolioItem.sort_order, PortfolioItem.headline)
    )
    return [portfolio_item_to_out(i) for i in result.scalars().all()]


@router.get("/public/{vendor_id}/profile-details", response_model=VendorProfileDetailsOut)
async def get_vendor_profile_details_public(vendor_id: str, db: AsyncSession = Depends(get_db)):
    vendor = await get_approved_vendor(db, vendor_id)
    if not vendor or vendor.status != ApprovalStatus.approved:
        raise HTTPException(status_code=404, detail="Vendor not found")
    row = await get_or_create_details(db, vendor_id)
    await db.commit()
    return details_to_out(row)


# ── Vendor self-service ──────────────────────────────────────

@router.get("/me", response_model=VendorOut)
async def get_my_profile(vendor: Vendor = Depends(get_current_vendor)):
    return vendor_to_out(vendor)


@router.put("/me", response_model=VendorOut)
async def update_my_profile(
    body: VendorUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    if "gallery_urls" in data:
        urls = validate_url_list(data.pop("gallery_urls"), max_count=MAX_GALLERY_IMAGES, field_name="gallery_urls")
        vendor.gallery_urls_json = dump_url_list(urls, max_count=MAX_GALLERY_IMAGES)
    for field, value in data.items():
        setattr(vendor, field, value)
    await db.commit()
    await db.refresh(vendor)
    return vendor_to_out(vendor)


@router.get("/me/profile-details", response_model=VendorProfileDetailsOut)
async def get_my_profile_details(vendor: Vendor = Depends(get_current_vendor), db: AsyncSession = Depends(get_db)):
    row = await get_or_create_details(db, vendor.id)
    await db.commit()
    return details_to_out(row)


@router.put("/me/profile-details", response_model=VendorProfileDetailsOut)
async def update_my_profile_details(
    body: VendorProfileDetailsUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    row = await get_or_create_details(db, vendor.id)
    apply_update(row, body)
    await db.commit()
    await db.refresh(row)
    return details_to_out(row)


# ── Service packages ─────────────────────────────────────────

@router.get("/me/packages", response_model=list[ServicePackageOut])
async def list_packages(vendor: Vendor = Depends(get_current_vendor), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServicePackage).where(ServicePackage.vendor_id == vendor.id))
    return result.scalars().all()


@router.post("/me/packages", response_model=ServicePackageOut, status_code=201)
async def create_package(
    body: ServicePackageCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    pkg = ServicePackage(vendor_id=vendor.id, **body.model_dump())
    db.add(pkg)
    await db.commit()
    await db.refresh(pkg)
    return pkg


@router.put("/me/packages/{pkg_id}", response_model=ServicePackageOut)
async def update_package(
    pkg_id: str,
    body: ServicePackageUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePackage).where(ServicePackage.id == pkg_id, ServicePackage.vendor_id == vendor.id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(pkg, field, value)
    await db.commit()
    await db.refresh(pkg)
    return pkg


@router.patch("/me/packages/{pkg_id}/toggle", response_model=ServicePackageOut)
async def toggle_package(
    pkg_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePackage).where(ServicePackage.id == pkg_id, ServicePackage.vendor_id == vendor.id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    pkg.active = not pkg.active
    await db.commit()
    await db.refresh(pkg)
    return pkg


@router.delete("/me/packages/{pkg_id}", status_code=204)
async def delete_package(
    pkg_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePackage).where(ServicePackage.id == pkg_id, ServicePackage.vendor_id == vendor.id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    await db.delete(pkg)
    await db.commit()


# ── Talent roster ────────────────────────────────────────────

@router.get("/me/roster", response_model=list[TalentMemberOut])
async def list_roster(vendor: Vendor = Depends(get_current_vendor), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TalentMember).where(TalentMember.vendor_id == vendor.id))
    return result.scalars().all()


@router.post("/me/roster", response_model=TalentMemberOut, status_code=201)
async def add_talent(
    body: TalentMemberCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    member = TalentMember(vendor_id=vendor.id, **body.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.put("/me/roster/{member_id}", response_model=TalentMemberOut)
async def update_talent(
    member_id: str,
    body: TalentMemberUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TalentMember).where(TalentMember.id == member_id, TalentMember.vendor_id == vendor.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Talent member not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/me/roster/{member_id}/availability", response_model=TalentMemberOut)
async def toggle_availability(
    member_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TalentMember).where(TalentMember.id == member_id, TalentMember.vendor_id == vendor.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Talent member not found")
    member.available = not member.available
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/me/roster/{member_id}", status_code=204)
async def delete_talent(
    member_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TalentMember).where(TalentMember.id == member_id, TalentMember.vendor_id == vendor.id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Talent member not found")
    await db.delete(member)
    await db.commit()


# ── Portfolio ────────────────────────────────────────────────

@router.get("/me/portfolio", response_model=list[PortfolioItemOut])
async def list_portfolio(vendor: Vendor = Depends(get_current_vendor), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.vendor_id == vendor.id)
        .order_by(PortfolioItem.featured.desc(), PortfolioItem.sort_order, PortfolioItem.headline)
    )
    return [portfolio_item_to_out(i) for i in result.scalars().all()]


@router.post("/me/portfolio", response_model=PortfolioItemOut, status_code=201)
async def create_portfolio_item(
    body: PortfolioItemCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    payload = body.model_dump()
    images = payload.pop("images", None)
    image_url = payload.pop("image_url", "")
    item = PortfolioItem(vendor_id=vendor.id, **payload)
    apply_portfolio_images(item, images=images if images else None, image_url=image_url if not images else None)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return portfolio_item_to_out(item)


@router.put("/me/portfolio/{item_id}", response_model=PortfolioItemOut)
async def update_portfolio_item(
    item_id: str,
    body: PortfolioItemUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PortfolioItem).where(PortfolioItem.id == item_id, PortfolioItem.vendor_id == vendor.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    payload = body.model_dump(exclude_none=True)
    images = payload.pop("images", None)
    image_url = payload.pop("image_url", None)
    for field, value in payload.items():
        setattr(item, field, value)
    if images is not None or image_url is not None:
        apply_portfolio_images(item, images=images, image_url=image_url)
    await db.commit()
    await db.refresh(item)
    return portfolio_item_to_out(item)


@router.patch("/me/portfolio/{item_id}/feature", response_model=PortfolioItemOut)
async def toggle_portfolio_feature(
    item_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PortfolioItem).where(PortfolioItem.id == item_id, PortfolioItem.vendor_id == vendor.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    item.featured = not item.featured
    await db.commit()
    await db.refresh(item)
    return portfolio_item_to_out(item)


@router.delete("/me/portfolio/{item_id}", status_code=204)
async def delete_portfolio_item(
    item_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PortfolioItem).where(PortfolioItem.id == item_id, PortfolioItem.vendor_id == vendor.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    await db.delete(item)
    await db.commit()


# ── Admin vendor management ───────────────────────────────────

@router.get("/admin", response_model=VendorListOut)
async def admin_list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    city: str | None = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Vendor)
    scoped_city = (admin.admin_city or "").strip() or (city or "").strip()
    if scoped_city:
        q = q.where(Vendor.city.ilike(f"%{scoped_city}%"))
    if status:
        q = q.where(Vendor.status == ApprovalStatus(status))
    if category:
        q = q.where(Vendor.category == category)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return VendorListOut(
        items=[vendor_to_out(v) for v in result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/{vendor_id}", response_model=VendorOut, dependencies=[Depends(get_current_admin)])
async def admin_get_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor_to_out(vendor)


@router.get("/admin/{vendor_id}/portfolio", dependencies=[Depends(get_current_admin)])
async def admin_get_vendor_portfolio(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    items = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.vendor_id == vendor_id)
        .order_by(PortfolioItem.featured.desc(), PortfolioItem.sort_order, PortfolioItem.headline)
    )
    return [portfolio_item_to_out(i) for i in items.scalars().all()]


@router.get("/admin/{vendor_id}/profile-details", response_model=VendorProfileDetailsOut, dependencies=[Depends(get_current_admin)])
async def admin_get_vendor_profile_details(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vendor not found")
    row = await get_or_create_details(db, vendor_id)
    await db.commit()
    return details_to_out(row)


@router.put("/admin/{vendor_id}/status", response_model=VendorOut)
async def admin_update_vendor_status(
    vendor_id: str,
    body: VendorStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.status = ApprovalStatus(body.status)
    await db.commit()
    await db.refresh(vendor)
    return vendor_to_out(vendor)


@router.put("/admin/{vendor_id}/kyc", response_model=VendorOut)
async def admin_update_vendor_kyc(
    vendor_id: str,
    body: VendorKycUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.kyc_verified = body.kyc_verified
    await db.commit()
    await db.refresh(vendor)
    return vendor_to_out(vendor)
