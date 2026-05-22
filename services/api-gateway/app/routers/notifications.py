import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.db.redis import get_redis
from app.models.segments import Notification
from app.models.user import User
from app.schemas.notifications import NotificationResponse
from app.schemas.pagination import Paginated
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("", response_model=Paginated[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        base = base.where(Notification.is_read.is_(False))

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)
    )
    items = list(items_result.scalars().all())
    return Paginated.build(items=items, total=total, page=page, page_size=page_size)


@router.post("/read-all", response_model=dict)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()
    return {"ok": True}


@router.post("/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        await db.commit()
    return {"ok": True}


async def publish_notification(notif: Notification) -> None:
    """Publish a newly created Notification to Redis so WS service fans it out."""
    try:
        r = get_redis()
        payload = {
            "user_id": str(notif.user_id),
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "body": notif.body,
            "is_read": False,
            "campaign_id": str(notif.campaign_id) if notif.campaign_id else None,
            "payload": notif.payload,
        }
        await r.publish("notifications", json.dumps(payload))
    except Exception:
        pass  # Non-critical — WS delivery is best-effort
