from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user, get_current_vendor
from app.models.review import Review
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.review import ReviewCreate, ReviewListOut, ReviewOut, ReviewReply

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/vendor", response_model=ReviewListOut)
async def list_vendor_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    q = select(Review).where(Review.vendor_id == vendor.id)
    all_result = await db.execute(q)
    all_reviews = all_result.scalars().all()
    avg = sum(r.stars for r in all_reviews) / len(all_reviews) if all_reviews else 0.0
    paginated = await db.execute(q.order_by(Review.date.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [ReviewOut.model_validate(r) for r in paginated.scalars().all()]
    return ReviewListOut(items=items, total=len(all_reviews), average_rating=avg)


@router.get("/admin", response_model=ReviewListOut, dependencies=[Depends(get_current_admin)])
async def admin_list_reviews(
    flagged: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Review)
    if flagged is not None:
        q = q.where(Review.flagged == flagged)
    all_result = await db.execute(q)
    all_reviews = all_result.scalars().all()
    avg = sum(r.stars for r in all_reviews) / len(all_reviews) if all_reviews else 0.0
    paginated = await db.execute(q.order_by(Review.date.desc()).offset((page - 1) * page_size).limit(page_size))
    return ReviewListOut(
        items=[ReviewOut.model_validate(r) for r in paginated.scalars().all()],
        total=len(all_reviews),
        average_rating=avg,
    )


@router.post("", response_model=ReviewOut, status_code=201)
async def create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = Review(
        author_id=current_user.id,
        vendor_id=body.vendor_id,
        booking_id=body.booking_id,
        stars=body.stars,
        text=body.text,
    )
    db.add(review)
    # Recalculate vendor rating
    result = await db.execute(select(Review).where(Review.vendor_id == body.vendor_id))
    existing = result.scalars().all()
    all_stars = [r.stars for r in existing] + [body.stars]
    vend_result = await db.execute(select(Vendor).where(Vendor.id == body.vendor_id))
    vendor = vend_result.scalar_one_or_none()
    if vendor:
        vendor.rating = sum(all_stars) / len(all_stars)
    await db.commit()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


@router.post("/{review_id}/reply", response_model=ReviewOut)
async def reply_to_review(
    review_id: str,
    body: ReviewReply,
    vendor: Vendor = Depends(get_current_vendor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.id == review_id, Review.vendor_id == vendor.id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.reply = body.reply
    await db.commit()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


@router.put("/{review_id}/flag", response_model=ReviewOut)
async def flag_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.flagged = not review.flagged
    await db.commit()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


@router.delete("/{review_id}", status_code=204)
async def delete_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.delete(review)
    await db.commit()
