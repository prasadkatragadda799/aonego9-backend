from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.models.vendor_profile import VendorProfileDetails


async def get_or_create_details(db: AsyncSession, vendor_id: str) -> VendorProfileDetails:
    result = await db.execute(select(VendorProfileDetails).where(VendorProfileDetails.vendor_id == vendor_id))
    row = result.scalar_one_or_none()
    if row:
        return row
    row = VendorProfileDetails(vendor_id=vendor_id)
    db.add(row)
    await db.flush()
    return row


async def get_approved_vendor(db: AsyncSession, vendor_id: str) -> Vendor | None:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        return None
    return vendor
