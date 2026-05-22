import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.campaign import Campaign
from app.models.segments import SegmentUpload
from app.models.user import User
from app.schemas.segments import SegmentUploadRequest, SegmentUploadResponse
from app.utils.deps import get_current_user

router = APIRouter()


@router.post("/upload", response_model=SegmentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_segment(
    payload: SegmentUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate campaign belongs to user
    campaign_id = uuid.UUID(payload.campaign_id)
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    seg = SegmentUpload(
        user_id=current_user.id,
        campaign_id=campaign_id,
        ad_platform=payload.ad_platform,
        lookalike=payload.lookalike,
        lookalike_scale=payload.lookalike_scale if payload.lookalike else None,
        min_roas_threshold=payload.min_roas_threshold,
        status="pending",
    )
    db.add(seg)
    await db.flush()

    # Dispatch Celery task
    from app.tasks.segmentation import upload_seed_segment
    task = upload_seed_segment.delay(
        task_id=str(seg.id),
        campaign_id=str(campaign_id),
        ad_platform=payload.ad_platform,
        lookalike=payload.lookalike,
        scale=payload.lookalike_scale or 5,
        min_roas=payload.min_roas_threshold,
    )
    seg.celery_task_id = task.id
    await db.commit()

    return SegmentUploadResponse(
        task_id=str(seg.id),
        campaign_id=str(seg.campaign_id),
        ad_platform=seg.ad_platform,
        seed_size=None,
        status=seg.status,  # type: ignore[arg-type]
        created_at=seg.created_at,
        updated_at=seg.updated_at,
    )


@router.get("", response_model=list[SegmentUploadResponse])
async def list_segments(
    campaign_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(SegmentUpload).where(SegmentUpload.user_id == current_user.id)
    if campaign_id:
        q = q.where(SegmentUpload.campaign_id == uuid.UUID(campaign_id))
    q = q.order_by(SegmentUpload.created_at.desc()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        SegmentUploadResponse(
            task_id=str(s.id),
            campaign_id=str(s.campaign_id),
            ad_platform=s.ad_platform,
            seed_size=s.seed_size,
            status=s.status,  # type: ignore[arg-type]
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in rows
    ]


@router.post("/preview")
async def preview_segment(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return estimated segment size given filter parameters (count query only)."""
    # In production: translate payload filters into a ClickHouse COUNT query.
    # Returning a stub here so the endpoint contract is established.
    campaign_id = payload.get("campaign_id")
    if campaign_id:
        result = await db.execute(
            select(SegmentUpload).where(
                SegmentUpload.campaign_id == uuid.UUID(campaign_id),
                SegmentUpload.user_id == current_user.id,
            )
        )
        count = len(result.scalars().all())
    else:
        count = 0
    return {"estimated_count": count, "note": "Preview is approximate"}


@router.get("/{segment_id}", response_model=SegmentUploadResponse)
async def get_segment(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SegmentUpload).where(
            SegmentUpload.id == uuid.UUID(segment_id),
            SegmentUpload.user_id == current_user.id,
        )
    )
    seg = result.scalar_one_or_none()
    if not seg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Segment not found")
    return SegmentUploadResponse(
        task_id=str(seg.id),
        campaign_id=str(seg.campaign_id),
        ad_platform=seg.ad_platform,
        seed_size=seg.seed_size,
        status=seg.status,  # type: ignore[arg-type]
        created_at=seg.created_at,
        updated_at=seg.updated_at,
    )
