from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.cms import Category, CmsBanner
from app.models.directory import AdCreative, LogoPartner, SocialAccount, TeamMember
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
from app.schemas.directory import (
    AdCreativeCreate,
    AdCreativeOut,
    AdCreativeToggle,
    AdCreativeUpdate,
    LogoPartnerCreate,
    LogoPartnerOut,
    LogoPartnerUpdate,
    PublishToggle,
    SocialAccountCreate,
    SocialAccountOut,
    SocialAccountUpdate,
    TeamMemberCreate,
    TeamMemberOut,
    TeamMemberUpdate,
)
from app.schemas.newsletter import (
    NewsletterContributionOut,
    NewsletterIssueCreate,
    NewsletterIssueOut,
    NewsletterIssueUpdate,
)

router = APIRouter(prefix="/cms", tags=["cms"])


# ── Banners ──────────────────────────────────────────────────

@router.get("/banners", response_model=list[CmsBannerOut], dependencies=[Depends(get_current_admin)])
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

@router.get("/categories", response_model=list[CategoryOut], dependencies=[Depends(get_current_admin)])
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


@router.get("/newsletters", response_model=list[NewsletterIssueOut], dependencies=[Depends(get_current_admin)])
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


# ── Ads ──────────────────────────────────────────────────────────

@router.get("/ads", response_model=list[AdCreativeOut], dependencies=[Depends(get_current_admin)])
async def list_ads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdCreative).order_by(AdCreative.created_at.desc()))
    return result.scalars().all()


@router.post("/ads", response_model=AdCreativeOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_ad(body: AdCreativeCreate, db: AsyncSession = Depends(get_db)):
    row = AdCreative(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.put("/ads/{ad_id}", response_model=AdCreativeOut)
async def update_ad(
    ad_id: str,
    body: AdCreativeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(AdCreative).where(AdCreative.id == ad_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Ad not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/ads/{ad_id}", response_model=AdCreativeOut)
async def toggle_ad_active(
    ad_id: str,
    body: AdCreativeToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(AdCreative).where(AdCreative.id == ad_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Ad not found")
    row.active = body.active
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/ads/{ad_id}", status_code=204)
async def delete_ad(
    ad_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(AdCreative).where(AdCreative.id == ad_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Ad not found")
    await db.delete(row)
    await db.commit()


# ── Partners ─────────────────────────────────────────────────────

@router.get("/partners", response_model=list[LogoPartnerOut], dependencies=[Depends(get_current_admin)])
async def list_partners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LogoPartner).order_by(LogoPartner.created_at.desc()))
    return result.scalars().all()


@router.post("/partners", response_model=LogoPartnerOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_partner(body: LogoPartnerCreate, db: AsyncSession = Depends(get_db)):
    row = LogoPartner(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.put("/partners/{partner_id}", response_model=LogoPartnerOut)
async def update_partner(
    partner_id: str,
    body: LogoPartnerUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(LogoPartner).where(LogoPartner.id == partner_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/partners/{partner_id}", response_model=LogoPartnerOut)
async def toggle_partner_published(
    partner_id: str,
    body: PublishToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(LogoPartner).where(LogoPartner.id == partner_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    row.published = body.published
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/partners/{partner_id}", status_code=204)
async def delete_partner(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(LogoPartner).where(LogoPartner.id == partner_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    await db.delete(row)
    await db.commit()


# ── Team ─────────────────────────────────────────────────────────

@router.get("/team", response_model=list[TeamMemberOut], dependencies=[Depends(get_current_admin)])
async def list_team(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamMember).order_by(TeamMember.created_at.desc()))
    return result.scalars().all()


@router.post("/team", response_model=TeamMemberOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_team_member(body: TeamMemberCreate, db: AsyncSession = Depends(get_db)):
    row = TeamMember(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.put("/team/{member_id}", response_model=TeamMemberOut)
async def update_team_member(
    member_id: str,
    body: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Team member not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/team/{member_id}", response_model=TeamMemberOut)
async def toggle_team_member_published(
    member_id: str,
    body: PublishToggle,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Team member not found")
    row.published = body.published
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/team/{member_id}", status_code=204)
async def delete_team_member(
    member_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Team member not found")
    await db.delete(row)
    await db.commit()


# ── Social accounts (admin-only — no public consumer) ────────────

@router.get("/social", response_model=list[SocialAccountOut], dependencies=[Depends(get_current_admin)])
async def list_social_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SocialAccount).order_by(SocialAccount.created_at.desc()))
    return result.scalars().all()


@router.post("/social", response_model=SocialAccountOut, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_social_account(body: SocialAccountCreate, db: AsyncSession = Depends(get_db)):
    row = SocialAccount(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.put("/social/{account_id}", response_model=SocialAccountOut)
async def update_social_account(
    account_id: str,
    body: SocialAccountUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SocialAccount).where(SocialAccount.id == account_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Social account not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/social/{account_id}", status_code=204)
async def delete_social_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(SocialAccount).where(SocialAccount.id == account_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Social account not found")
    await db.delete(row)
    await db.commit()
