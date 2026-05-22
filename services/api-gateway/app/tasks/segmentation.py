import logging
import sys
import os
import uuid

from app.celery import celery

log = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@celery.task(name="app.tasks.segmentation.upload_seed_segment")
def upload_seed_segment(
    task_id: str, campaign_id: str, ad_platform: str,
    lookalike: bool, scale: int, min_roas: float = 3.0,
):
    """
    Основная задача загрузки сегмента:
    1. Получает seed из ClickHouse (атрибутированные покупатели кампании).
    2. Если lookalike=True — строит look-alike через ML-модель.
    3. Загружает идентификаторы в рекламный кабинет через коннектор.
    4. Обновляет статус SegmentUpload в PostgreSQL.
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(
        _run(task_id, campaign_id, ad_platform, lookalike, scale, min_roas)
    )


async def _run(task_id, campaign_id, ad_platform, lookalike, scale, min_roas):
    from app.db.postgres import AsyncSessionLocal
    from app.models.segments import SegmentUpload
    from app.models.connections import AdPlatformConnection
    from app.utils.crypto import decrypt_token
    from services.ingestion.registry import make_ad_connector
    from services.ml.shared.ch_client import get_ch
    from sqlalchemy import select, update
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        seg_result = await db.execute(
            select(SegmentUpload).where(SegmentUpload.id == uuid.UUID(task_id))
        )
        seg = seg_result.scalar_one_or_none()
        if not seg:
            log.error("SegmentUpload %s not found", task_id)
            return

        # Получаем credentials для платформы
        conn_result = await db.execute(
            select(AdPlatformConnection).where(
                AdPlatformConnection.user_id == seg.user_id,
                AdPlatformConnection.platform == ad_platform,
                AdPlatformConnection.is_active.is_(True),
            )
        )
        conn = conn_result.scalar_one_or_none()

    if not conn:
        await _update_status(task_id, "failed", error=f"No active connection for {ad_platform}")
        return

    try:
        await _update_status(task_id, "processing")

        # Получаем seed: visitor_hash покупателей с ROAS >= min_roas
        identifiers = _get_seed_identifiers(campaign_id, min_roas)

        if lookalike and len(identifiers) >= 10:
            from services.ml.lookalike.model import build_segment
            segment = build_segment(campaign_id=campaign_id, min_roas=min_roas, scale=scale)
            identifiers = segment.visitor_hashes

        if not identifiers:
            await _update_status(task_id, "failed", error="Empty segment")
            return

        # Загружаем в кабинет
        credentials = _build_credentials(conn, decrypt_token)
        connector = make_ad_connector(ad_platform, credentials)
        external_id = await connector.upload_audience(task_id, identifiers)

        await _update_status(
            task_id, "uploaded",
            seed_size=len(identifiers),
            external_segment_id=external_id,
        )
        log.info("Segment %s uploaded: %d identifiers → %s (%s)",
                 task_id, len(identifiers), external_id, ad_platform)

    except NotImplementedError as exc:
        await _update_status(task_id, "failed", error=str(exc))
    except Exception as exc:
        log.error("Segment upload failed: %s", exc)
        await _update_status(task_id, "failed", error=str(exc))


def _get_seed_identifiers(campaign_id: str, min_roas: float) -> list[str]:
    """Возвращает visitor_hash покупателей, у которых ROAS >= min_roas."""
    from services.ml.shared.ch_client import get_ch
    ch = get_ch()
    rows = ch.query("""
        SELECT DISTINCT c.visitor_hash
        FROM clicks c
        JOIN attributions a ON a.trax_id = c.trax_id
        JOIN marketplace_orders mo ON mo.order_id = a.order_id
        JOIN ad_stats ads ON ads.campaign_id = a.campaign_id
            AND toDate(ads.stat_date) = toDate(c.ts)
        WHERE a.campaign_id = %(cid)s
          AND ads.spend > 0
          AND mo.order_amount / ads.spend >= %(roas)s
        LIMIT 100000
    """, parameters={"cid": campaign_id, "roas": min_roas}).result_rows
    return [r[0] for r in rows]


def _build_credentials(conn, decrypt_fn) -> dict:
    creds = {"access_token": decrypt_fn(conn.access_token_enc)}
    if conn.account_id:
        creds["account_id"] = conn.account_id
    if conn.account_name and conn.platform == "yandex_direct":
        creds["client_login"] = conn.account_name
    return creds


async def _update_status(task_id: str, status: str,
                         seed_size: int | None = None,
                         external_segment_id: str | None = None,
                         error: str | None = None):
    from app.db.postgres import AsyncSessionLocal
    from app.models.segments import SegmentUpload
    from sqlalchemy import update
    from datetime import datetime, timezone

    values: dict = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if seed_size is not None:
        values["seed_size"] = seed_size
    if external_segment_id is not None:
        values["external_segment_id"] = external_segment_id
    if error is not None:
        values["error_message"] = error

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(SegmentUpload)
            .where(SegmentUpload.id == uuid.UUID(task_id))
            .values(**values)
        )
        await db.commit()
