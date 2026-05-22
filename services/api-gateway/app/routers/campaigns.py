from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.schemas.campaigns import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    TrackingLinkCreate, TrackingLinkResponse,
)
from app.schemas.pagination import Paginated
from app.services import campaigns as svc
from app.utils.deps import get_current_user
from app.utils.trax import build_tracking_url

router = APIRouter()


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await svc.create_campaign(db, current_user.id, payload)


@router.get("", response_model=Paginated[CampaignResponse])
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await svc.list_campaigns(db, current_user.id, page=page, page_size=page_size)
    return Paginated.build(items=items, total=total, page=page, page_size=page_size)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await svc.get_campaign(db, current_user.id, campaign_id)
    if not campaign:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await svc.update_campaign(db, current_user.id, campaign_id, payload)
    if not campaign:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await svc.delete_campaign(db, current_user.id, campaign_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")


@router.get("/{campaign_id}/links", response_model=list[TrackingLinkResponse])
async def get_tracking_links(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    links = await svc.get_tracking_links(db, current_user.id, campaign_id)
    return [
        TrackingLinkResponse(
            trax_id=link.trax_id,
            tracking_url=build_tracking_url(link.trax_id),
            destination_url=link.destination_url,
            label=link.label,
            created_at=link.created_at,
        )
        for link in links
    ]


@router.post("/{campaign_id}/links", response_model=TrackingLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_tracking_link(
    campaign_id: str,
    payload: TrackingLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await svc.create_tracking_link(db, current_user.id, campaign_id, payload)
    if not link:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return TrackingLinkResponse(
        trax_id=link.trax_id,
        tracking_url=build_tracking_url(link.trax_id),
        destination_url=link.destination_url,
        label=link.label,
        created_at=link.created_at,
    )
