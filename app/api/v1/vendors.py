from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_vendor
from app.models.user import ApprovalStatus, User
from app.models.vendor import ServicePackage, TalentMember, Vendor
from app.schemas.vendor import (
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
    return result.scalars().all()


@router.get("/public/{vendor_id}", response_model=VendorPublicOut)
async def get_vendor_public(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.status == ApprovalStatus.approved))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


# ── Vendor self-service ──────────────────────────────────────

@router.get("/me", response_model=VendorOut)
async def get_my_profile(vendor: Vendor = Depends(get_current_vendor)):
    return vendor


@router.put("/me", response_model=VendorOut)
async def update_my_profile(
    body: VendorUpdate,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
    await db.commit()
    await db.refresh(vendor)
    return vendor


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


# ── Admin vendor management ───────────────────────────────────

@router.get("/admin", response_model=VendorListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Vendor)
    if status:
        q = q.where(Vendor.status == ApprovalStatus(status))
    if category:
        q = q.where(Vendor.category == category)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return VendorListOut(items=result.scalars().all(), total=total, page=page, page_size=page_size)


@router.get("/admin/{vendor_id}", response_model=VendorOut, dependencies=[Depends(get_current_admin)])
async def admin_get_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


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
    return vendor


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
    return vendor
