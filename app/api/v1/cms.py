from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.cms import Category, CmsBanner
from app.models.newsletter import NewsletterContribution, NewsletterIssue
from app.models.user import User
from app.schemas.cms import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    CmsBannerCreate,
    CmsBannerOut,
    CmsBannerUpdate,
)
from app.schemas.newsletter import (
    NewsletterContributionOut,
    NewsletterIssueCreate,
    NewsletterIssueOut,
    NewsletterIssueUpdate,
)

router = APIRouter(prefix="/cms", tags=["cms"])


# ── Banners ──────────────────────────────────────────────────

@router.get("/banners", response_model=list[CmsBannerOut])
async def list_banners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CmsBanner).order_by(CmsBanner.sort_order))
    return result.scalars().all()


@router.post("/banners", response_model=CmsBannerOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_banner(body: CmsBannerCreate, db: AsyncSession = Depends(get_db)):
    banner = CmsBanner(**body.model_dump())
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.put("/banners/{banner_id}", response_model=CmsBannerOut)
async def update_banner(
    banner_id: str,
    body: CmsBannerUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(CmsBanner).where(CmsBanner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(banner, field, value)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.delete("/banners/{banner_id}", status_code=204)
async def delete_banner(
    banner_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(CmsBanner).where(CmsBanner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    await db.delete(banner)
    await db.commit()


# ── Categories ───────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.sort_order))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = Category(**body.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/categories/{cat_id}", response_model=CategoryOut)
async def update_category(
    cat_id: str,
    body: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.patch("/categories/{cat_id}/toggle", response_model=CategoryOut)
async def toggle_category(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.active = not cat.active
    await db.commit()
    await db.refresh(cat)
    return cat


# ── Newsletter ───────────────────────────────────────────────


@router.get("/newsletters", response_model=list[NewsletterIssueOut])
async def list_newsletters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsletterIssue).order_by(NewsletterIssue.published_at.desc()))
    return [NewsletterIssueOut.from_row(r) for r in result.scalars().all()]


@router.post("/newsletters", response_model=NewsletterIssueOut, status_code=201)
async def publish_newsletter(
    body: NewsletterIssueCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    published = datetime.now(timezone.utc)
    if body.date:
        try:
            published = datetime.fromisoformat(body.date).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    row = NewsletterIssue(
        kind=body.kind,
        title=body.title,
        excerpt=body.excerpt,
        body=body.body,
        tag=body.tag,
        city=body.city,
        emoji=body.emoji,
        bg=body.bg,
        image_url=body.image_url,
        author=body.author,
        author_email=body.author_email,
        organisation=body.organisation,
        credentials_url=body.credentials_url,
        published_at=published,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return NewsletterIssueOut.from_row(row)


@router.put("/newsletters/{issue_id}", response_model=NewsletterIssueOut)
async def update_newsletter(
    issue_id: str,
    body: NewsletterIssueUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(NewsletterIssue).where(NewsletterIssue.id == issue_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return NewsletterIssueOut.from_row(row)


@router.delete("/newsletters/{issue_id}", status_code=204)
async def delete_newsletter(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(NewsletterIssue).where(NewsletterIssue.id == issue_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    await db.delete(row)
    await db.commit()


@router.get("/newsletters/contributions", response_model=list[NewsletterContributionOut])
async def list_contributions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(NewsletterContribution).order_by(NewsletterContribution.created_at.desc())
    )
    return result.scalars().all()
