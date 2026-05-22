"""
Загружает аудиторию в рекламный кабинет через коннекторы из services/ingestion.
Запускается как отдельный async worker, читает задания из Redis-очереди.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
import clickhouse_connect

from config import settings
from db import AsyncSessionLocal

log = logging.getLogger(__name__)

# Allow imports of services/ingestion and services/api-gateway
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_API_GW = os.path.join(_ROOT, "services", "api-gateway")
for _p in (_ROOT, _API_GW):
    if _p not in sys.path:
        sys.path.insert(0, _p)


async def run_worker():
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    log.info("Segmentation worker started. Listening on '%s'", settings.segment_queue_key)

    while True:
        try:
            item = await r.blpop(settings.segment_queue_key, timeout=settings.worker_poll_interval)
            if item is None:
                continue
            _, raw = item
            job = json.loads(raw)
            await process_job(job)
        except Exception as exc:
            log.error("Worker error: %s", exc)
            await asyncio.sleep(1)


async def process_job(job: dict):
    task_id: str = job["task_id"]
    campaign_id: str = job["campaign_id"]
    ad_platform: str = job["ad_platform"]
    lookalike: bool = job.get("lookalike", False)
    scale: int = job.get("scale", 5)
    min_roas: float = job.get("min_roas", 3.0)

    log.info("Processing segment job %s (platform=%s, lookalike=%s)", task_id, ad_platform, lookalike)

    async with AsyncSessionLocal() as db:
        await _set_status(db, task_id, "processing")
        conn_data = await _get_connection(db, campaign_id, ad_platform)
        if not conn_data:
            await _set_status(
                db, task_id, "failed",
                error=f"No active {ad_platform} connection for campaign {campaign_id}",
            )
            return

    try:
        identifiers = _get_seed(campaign_id, min_roas)

        if lookalike and len(identifiers) >= 10:
            from services.ml.lookalike.model import build_segment
            segment = build_segment(campaign_id=campaign_id, min_roas=min_roas, scale=scale)
            identifiers = segment.visitor_hashes

        if not identifiers:
            async with AsyncSessionLocal() as db:
                await _set_status(
                    db, task_id, "failed",
                    error="Empty segment — no attributed buyers found",
                )
            return

        from services.ingestion.registry import make_ad_connector
        connector = make_ad_connector(ad_platform, conn_data)
        external_id = await connector.upload_audience(task_id, identifiers)

        async with AsyncSessionLocal() as db:
            await _set_status(
                db, task_id, "uploaded",
                seed_size=len(identifiers),
                external_segment_id=external_id,
            )
        log.info("Segment %s uploaded: %d ids → %s", task_id, len(identifiers), external_id)

    except Exception as exc:
        log.exception("Segment job %s failed", task_id)
        async with AsyncSessionLocal() as db:
            await _set_status(db, task_id, "failed", error=str(exc)[:500])


async def _get_connection(db, campaign_id: str, ad_platform: str) -> dict | None:
    """
    Looks up the active ad-platform connection for the campaign's owner,
    decrypts the stored token, and returns a credentials dict.
    """
    from sqlalchemy import text
    from app.utils.crypto import decrypt_token

    result = await db.execute(
        text("""
            SELECT
                apc.access_token_enc,
                apc.refresh_token_enc,
                apc.account_id,
                apc.account_name,
                apc.platform
            FROM campaigns cam
            JOIN ad_platform_connections apc
              ON apc.user_id = cam.user_id
             AND apc.platform = :platform
             AND apc.is_active = TRUE
            WHERE cam.id = :campaign_id
            LIMIT 1
        """),
        {"campaign_id": campaign_id, "platform": ad_platform},
    )
    row = result.fetchone()
    if not row:
        return None

    creds: dict = {"access_token": decrypt_token(row.access_token_enc)}
    if row.refresh_token_enc:
        creds["refresh_token"] = decrypt_token(row.refresh_token_enc)
    if row.account_id:
        creds["account_id"] = row.account_id
    if row.account_name:
        if ad_platform == "yandex_direct":
            creds["client_login"] = row.account_name
        else:
            creds["account_name"] = row.account_name
    return creds


def _get_seed(campaign_id: str, min_roas: float) -> list[str]:
    ch = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_db,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )
    rows = ch.query(
        """
        SELECT DISTINCT c.visitor_hash
        FROM clicks c
        JOIN attributions a ON a.trax_id = c.trax_id
        JOIN marketplace_orders mo ON mo.order_id = a.order_id
        WHERE a.campaign_id = {campaign_id:String}
          AND mo.order_amount > 0
        LIMIT 100000
        """,
        parameters={"campaign_id": campaign_id},
    ).result_rows
    return [r[0] for r in rows if r[0]]


async def _set_status(
    db,
    task_id: str,
    status: str,
    seed_size: int | None = None,
    external_segment_id: str | None = None,
    error: str | None = None,
):
    from sqlalchemy import text

    values: dict = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
        "task_id": uuid.UUID(task_id),
    }
    set_parts = ["status = :status", "updated_at = :updated_at"]

    if seed_size is not None:
        set_parts.append("seed_size = :seed_size")
        values["seed_size"] = seed_size
    if external_segment_id is not None:
        set_parts.append("external_segment_id = :external_segment_id")
        values["external_segment_id"] = external_segment_id
    if error is not None:
        set_parts.append("error_message = :error_message")
        values["error_message"] = error

    await db.execute(
        text(f"UPDATE segment_uploads SET {', '.join(set_parts)} WHERE id = :task_id"),
        values,
    )
    await db.commit()
