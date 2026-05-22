import asyncio
import json
import logging
from datetime import date, timedelta

from app.celery import celery
from app.db.postgres import AsyncSessionLocal
from app.db.clickhouse import get_clickhouse
from app.db.redis import get_redis

log = logging.getLogger(__name__)


@celery.task(name="app.tasks.ingestion.fetch_all_ad_stats", bind=True, max_retries=3)
def fetch_all_ad_stats(self):
    """Сбор статистики по всем активным рекламным кабинетам пользователей."""
    asyncio.get_event_loop().run_until_complete(_fetch_all_ad_stats())


@celery.task(name="app.tasks.ingestion.fetch_all_marketplace_orders", bind=True, max_retries=3)
def fetch_all_marketplace_orders(self):
    """Сбор заказов из всех подключённых маркетплейсов."""
    asyncio.get_event_loop().run_until_complete(_fetch_all_marketplace_orders())


@celery.task(name="app.tasks.ingestion.fetch_ad_stats_for_connection")
def fetch_ad_stats_for_connection(connection_id: str, date_from: str, date_to: str):
    """Сбор статистики для одного конкретного подключения (запускается вручную)."""
    asyncio.get_event_loop().run_until_complete(
        _fetch_ad_stats_for_connection(connection_id, date_from, date_to)
    )


@celery.task(name="app.tasks.ingestion.fetch_marketplace_orders_for_connection")
def fetch_marketplace_orders_for_connection(connection_id: str, date_from: str, date_to: str):
    asyncio.get_event_loop().run_until_complete(
        _fetch_marketplace_orders_for_connection(connection_id, date_from, date_to)
    )


# ─── Async implementations ────────────────────────────────────────────────────

async def _fetch_all_ad_stats():
    from app.models.connections import AdPlatformConnection
    from app.utils.crypto import decrypt_token
    from services.ingestion.registry import make_ad_connector
    from sqlalchemy import select

    date_to = date.today() - timedelta(days=1)
    date_from = date_to - timedelta(days=1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdPlatformConnection).where(AdPlatformConnection.is_active.is_(True))
        )
        connections = result.scalars().all()

    for conn in connections:
        try:
            credentials = _build_ad_credentials(conn, decrypt_token)
            connector = make_ad_connector(conn.platform, credentials)
            stats = await connector.fetch_stats(date_from, date_to)
            await _write_ad_stats_to_clickhouse(stats, str(conn.user_id))
            await _update_last_synced(conn.id)
            log.info("Fetched %d ad stat rows for connection %s", len(stats), conn.id)
        except Exception as exc:
            log.error("Failed to fetch ad stats for connection %s: %s", conn.id, exc)


async def _fetch_all_marketplace_orders():
    from app.models.connections import MarketplaceConnection
    from app.utils.crypto import decrypt_token
    from services.ingestion.registry import make_marketplace_connector
    from sqlalchemy import select

    date_to = date.today()
    date_from = date_to - timedelta(days=2)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MarketplaceConnection).where(MarketplaceConnection.is_active.is_(True))
        )
        connections = result.scalars().all()

    for conn in connections:
        try:
            credentials = _build_mp_credentials(conn, decrypt_token)
            connector = make_marketplace_connector(conn.marketplace, credentials)
            orders = await connector.fetch_orders(date_from, date_to)
            await _write_orders_to_clickhouse(orders, str(conn.user_id))
            await _update_last_synced_mp(conn.id)
            log.info("Fetched %d orders for connection %s", len(orders), conn.id)
        except Exception as exc:
            log.error("Failed to fetch orders for connection %s: %s", conn.id, exc)


async def _fetch_ad_stats_for_connection(connection_id: str, date_from_str: str, date_to_str: str):
    from app.models.connections import AdPlatformConnection
    from app.utils.crypto import decrypt_token
    from services.ingestion.registry import make_ad_connector
    from sqlalchemy import select
    import uuid

    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdPlatformConnection).where(
                AdPlatformConnection.id == uuid.UUID(connection_id)
            )
        )
        conn = result.scalar_one_or_none()

    if not conn:
        log.warning("Connection %s not found", connection_id)
        return

    credentials = _build_ad_credentials(conn, decrypt_token)
    connector = make_ad_connector(conn.platform, credentials)
    stats = await connector.fetch_stats(date_from, date_to)
    await _write_ad_stats_to_clickhouse(stats, str(conn.user_id))


async def _fetch_marketplace_orders_for_connection(connection_id: str, date_from_str: str, date_to_str: str):
    from app.models.connections import MarketplaceConnection
    from app.utils.crypto import decrypt_token
    from services.ingestion.registry import make_marketplace_connector
    from sqlalchemy import select
    import uuid

    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MarketplaceConnection).where(
                MarketplaceConnection.id == uuid.UUID(connection_id)
            )
        )
        conn = result.scalar_one_or_none()

    if not conn:
        return

    credentials = _build_mp_credentials(conn, decrypt_token)
    connector = make_marketplace_connector(conn.marketplace, credentials)
    orders = await connector.fetch_orders(date_from, date_to)
    await _write_orders_to_clickhouse(orders, str(conn.user_id))


# ─── ClickHouse writers ───────────────────────────────────────────────────────

async def _write_ad_stats_to_clickhouse(stats, user_id: str):
    if not stats:
        return
    ch = get_clickhouse()
    rows = [
        [
            s.stat_date, s.ad_platform, user_id,
            "", s.external_campaign_id, s.external_ad_id, s.ad_name,
            s.impressions, s.clicks, s.spend, s.currency,
            s.ctr, s.cpc, s.conversions, s.conversion_value,
        ]
        for s in stats
    ]
    ch.insert(
        "ad_stats",
        rows,
        column_names=[
            "stat_date", "ad_platform", "user_id",
            "campaign_id", "external_campaign_id", "external_ad_id", "ad_name",
            "impressions", "clicks", "spend", "currency",
            "ctr", "cpc", "conversions", "conversion_value",
        ],
    )


async def _write_orders_to_clickhouse(orders, user_id: str):
    if not orders:
        return
    ch = get_clickhouse()
    rows = [
        [
            o.order_id, o.marketplace, user_id, o.product_id, o.sku,
            o.quantity, o.order_amount, o.currency, o.order_status,
            o.ordered_at, o.delivered_at,
        ]
        for o in orders
    ]
    ch.insert(
        "marketplace_orders",
        rows,
        column_names=[
            "order_id", "marketplace", "user_id", "product_id", "sku",
            "quantity", "order_amount", "currency", "order_status",
            "ordered_at", "delivered_at",
        ],
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_ad_credentials(conn, decrypt_fn) -> dict:
    creds = {"access_token": decrypt_fn(conn.access_token_enc)}
    if conn.refresh_token_enc:
        creds["refresh_token"] = decrypt_fn(conn.refresh_token_enc)
    if conn.account_id:
        creds["account_id"] = conn.account_id
    # Яндекс.Директ требует client_login
    if conn.platform == "yandex_direct" and conn.account_name:
        creds["client_login"] = conn.account_name
    return creds


def _build_mp_credentials(conn, decrypt_fn) -> dict:
    creds = {"api_key": decrypt_fn(conn.api_key_enc)}
    if conn.client_id:
        creds["client_id"] = conn.client_id
    if conn.seller_id:
        creds["seller_id"] = conn.seller_id
    return creds


async def _update_last_synced(connection_id):
    from app.models.connections import AdPlatformConnection
    from sqlalchemy import update
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(AdPlatformConnection)
            .where(AdPlatformConnection.id == connection_id)
            .values(last_synced_at=datetime.now(timezone.utc))
        )
        await db.commit()


async def _update_last_synced_mp(connection_id):
    from app.models.connections import MarketplaceConnection
    from sqlalchemy import update
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(MarketplaceConnection)
            .where(MarketplaceConnection.id == connection_id)
            .values(last_synced_at=datetime.now(timezone.utc))
        )
        await db.commit()
