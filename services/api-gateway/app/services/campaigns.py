"""
Бизнес-логика кампаний:
- CRUD в PostgreSQL
- Генерация trax_id и трекинг-ссылок
- Кэширование destination_url в Redis (читается tracking-сервисом)
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.models.campaign import Campaign, TrackingLink
from app.schemas.campaigns import CampaignCreate, CampaignUpdate, TrackingLinkCreate
from app.utils.trax import generate_trax_id, build_tracking_url

# TTL записи в Redis — 2 года в секундах (совпадает с TTL таблицы clicks в CH)
_REDIS_TTL = 60 * 60 * 24 * 365 * 2


async def create_campaign(
    db: AsyncSession, user_id: uuid.UUID, payload: CampaignCreate
) -> Campaign:
    campaign = Campaign(
        user_id=user_id,
        name=payload.name,
        marketplace=payload.marketplace.value,
        ad_platform=payload.ad_platform.value,
        destination_url=str(payload.destination_url),
        budget=payload.budget,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
    )
    db.add(campaign)
    await db.flush()  # получаем campaign.id

    # Создаём первую трекинг-ссылку автоматически
    await _create_link(
        db=db,
        campaign=campaign,
        destination_url=str(payload.destination_url),
        label="default",
        utm_content=None,
        utm_term=None,
    )

    await db.commit()
    await db.refresh(campaign)
    return campaign


async def list_campaigns(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Campaign], int]:
    base = select(Campaign).where(Campaign.user_id == user_id)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        base.order_by(Campaign.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(items_result.scalars().all()), total


async def get_campaign(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: str
) -> Campaign | None:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == uuid.UUID(campaign_id),
            Campaign.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_campaign(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: str, payload: CampaignUpdate
) -> Campaign | None:
    campaign = await get_campaign(db, user_id, campaign_id)
    if not campaign:
        return None

    updates = payload.model_dump(exclude_none=True)
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        await db.execute(
            update(Campaign)
            .where(Campaign.id == uuid.UUID(campaign_id))
            .values(**updates)
        )
        await db.commit()
        await db.refresh(campaign)

    return campaign


async def delete_campaign(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: str
) -> bool:
    campaign = await get_campaign(db, user_id, campaign_id)
    if not campaign:
        return False

    # Удаляем ключи из Redis для всех ссылок кампании
    links_result = await db.execute(
        select(TrackingLink).where(TrackingLink.campaign_id == uuid.UUID(campaign_id))
    )
    links = links_result.scalars().all()
    if links:
        redis = get_redis()
        await redis.delete(*[f"trax:dest:{link.trax_id}" for link in links])

    await db.execute(
        delete(Campaign).where(Campaign.id == uuid.UUID(campaign_id))
    )
    await db.commit()
    return True


async def get_tracking_links(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: str
) -> list[TrackingLink]:
    campaign = await get_campaign(db, user_id, campaign_id)
    if not campaign:
        return []

    result = await db.execute(
        select(TrackingLink)
        .where(TrackingLink.campaign_id == uuid.UUID(campaign_id))
        .order_by(TrackingLink.created_at)
    )
    return list(result.scalars().all())


async def create_tracking_link(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: str, payload: TrackingLinkCreate
) -> TrackingLink | None:
    campaign = await get_campaign(db, user_id, campaign_id)
    if not campaign:
        return None

    destination = str(payload.destination_url) if payload.destination_url else campaign.destination_url
    link = await _create_link(
        db=db,
        campaign=campaign,
        destination_url=destination,
        label=payload.label,
        utm_content=payload.utm_content,
        utm_term=payload.utm_term,
    )
    await db.commit()
    await db.refresh(link)
    return link


# ─── internal ─────────────────────────────────────────────────────────────────

async def _create_link(
    db: AsyncSession,
    campaign: Campaign,
    destination_url: str,
    label: str | None,
    utm_content: str | None,
    utm_term: str | None,
) -> TrackingLink:
    trax_id = await _unique_trax_id(db)

    # Собираем финальный URL с UTM-параметрами
    final_url = _append_utm(
        url=destination_url,
        source=campaign.utm_source or campaign.ad_platform,
        medium=campaign.utm_medium or "cpc",
        campaign_name=campaign.utm_campaign or campaign.name,
        content=utm_content,
        term=utm_term,
        trax_id=trax_id,
    )

    link = TrackingLink(
        trax_id=trax_id,
        campaign_id=campaign.id,
        destination_url=final_url,
        utm_source=campaign.utm_source,
        utm_medium=campaign.utm_medium,
        utm_campaign=campaign.utm_campaign,
        utm_content=utm_content,
        utm_term=utm_term,
        label=label,
    )
    db.add(link)
    await db.flush()

    # Кэшируем в Redis — tracking-сервис читает отсюда при каждом клике
    redis = get_redis()
    await redis.set(f"trax:dest:{trax_id}", final_url, ex=_REDIS_TTL)
    # Дополнительно кэшируем метаданные для обогащения клика в ETL
    await redis.hset(f"trax:meta:{trax_id}", mapping={
        "campaign_id": str(campaign.id),
        "user_id": str(campaign.user_id),
        "ad_platform": campaign.ad_platform,
        "marketplace": campaign.marketplace,
    })
    await redis.expire(f"trax:meta:{trax_id}", _REDIS_TTL)

    return link


async def _unique_trax_id(db: AsyncSession) -> str:
    """Генерирует trax_id, гарантированно уникальный в БД."""
    for _ in range(10):
        trax_id = generate_trax_id()
        exists = await db.execute(
            select(TrackingLink.trax_id).where(TrackingLink.trax_id == trax_id)
        )
        if not exists.scalar_one_or_none():
            return trax_id
    raise RuntimeError("Failed to generate unique trax_id after 10 attempts")


def _append_utm(
    url: str, source: str, medium: str, campaign_name: str,
    content: str | None, term: str | None, trax_id: str,
) -> str:
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    params.setdefault("utm_source", [source])
    params.setdefault("utm_medium", [medium])
    params.setdefault("utm_campaign", [campaign_name])
    params["trax_id"] = [trax_id]
    if content:
        params.setdefault("utm_content", [content])
    if term:
        params.setdefault("utm_term", [term])

    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))
