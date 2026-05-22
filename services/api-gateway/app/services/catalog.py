"""
Catalog Sync Service — синхронизация каталога товаров из маркетплейсов.

Алгоритм:
  1. Берём все активные MarketplaceConnection с их Store.
  2. Для каждой — вызываем connector.fetch_products().
  3. Upsert в таблицу products по (store_id, external_product_id).
  4. Артикулы, которых нет в свежей выгрузке — помечаем is_archived=True.
  5. Дочерние артикулы, чей parent исчез — is_orphaned=True.
  6. Обновляем store.last_sync_at.
"""
import logging
import sys
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import AsyncSessionLocal
from app.models.catalog import Store, Product
from app.models.connections import MarketplaceConnection
from app.utils.crypto import decrypt_token as decrypt_value

log = logging.getLogger(__name__)

# Add project root for ingestion imports
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _build_connector(conn: MarketplaceConnection):
    """Создаёт коннектор маркетплейса по записи из БД."""
    api_key = decrypt_value(conn.api_key_enc)

    if conn.marketplace == "ozon":
        from services.ingestion.connectors.ozon.connector import OzonConnector
        return OzonConnector(client_id=conn.client_id or "", api_key=api_key)

    if conn.marketplace == "wildberries":
        from services.ingestion.connectors.wildberries.connector import WildberriesConnector
        return WildberriesConnector(api_key=api_key)

    if conn.marketplace == "yandex_market":
        from services.ingestion.connectors.yandex_market.connector import YandexMarketConnector
        return YandexMarketConnector(
            oauth_token=api_key,
            client_id=conn.client_id or "",
            campaign_id=conn.seller_id or "",
        )

    if conn.marketplace == "amazon":
        from services.ingestion.connectors.amazon.connector import AmazonConnector
        # api_key_enc хранит refresh_token; client_id / seller_id — client_id и client_secret
        return AmazonConnector(
            refresh_token=api_key,
            client_id=conn.client_id or "",
            client_secret=conn.seller_id or "",
        )

    raise ValueError(f"Unknown marketplace: {conn.marketplace}")


async def sync_store_catalog(store: Store, conn: MarketplaceConnection) -> int:
    """
    Синхронизирует каталог одного магазина.
    Возвращает количество затронутых товаров.
    """
    try:
        connector = _build_connector(conn)
        products = await connector.fetch_products()
    except Exception as exc:
        log.error("Catalog fetch failed for store %s (%s): %s", store.id, store.provider, exc)
        raise

    async with AsyncSessionLocal() as db:
        fresh_ids = {p.external_product_id for p in products}

        # ── upsert fresh products ─────────────────────────────────────────────
        for prod in products:
            stmt = pg_insert(Product).values(
                id=uuid.uuid4(),
                user_id=store.user_id,
                store_id=store.id,
                provider=store.provider,
                external_product_id=prod.external_product_id,
                parent_external_id=prod.parent_external_id or None,
                title=prod.title,
                price=prod.price,
                stock=prod.stock,
                image_url=prod.image_url or None,
                has_variations=prod.has_variations,
                is_active=True,
                is_archived=False,
                is_orphaned=False,
                last_sync_at=datetime.now(timezone.utc),
            ).on_conflict_do_update(
                constraint="uq_products_store_external_id",
                set_={
                    "title": prod.title,
                    "price": prod.price,
                    "stock": prod.stock,
                    "image_url": prod.image_url or None,
                    "has_variations": prod.has_variations,
                    "parent_external_id": prod.parent_external_id or None,
                    "is_active": True,
                    "is_archived": False,
                    "is_orphaned": False,
                    "last_sync_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await db.execute(stmt)

        # ── archive products no longer in fresh feed ──────────────────────────
        result = await db.execute(
            select(Product).where(
                Product.store_id == store.id,
                Product.is_archived.is_(False),
            )
        )
        existing = result.scalars().all()
        archived_parents: set[str] = set()

        for p in existing:
            if p.external_product_id not in fresh_ids:
                p.is_archived = True
                if p.parent_external_id is None:
                    archived_parents.add(p.external_product_id)

        # ── orphan children whose parent was archived ─────────────────────────
        if archived_parents:
            await db.execute(
                update(Product)
                .where(
                    Product.store_id == store.id,
                    Product.parent_external_id.in_(archived_parents),
                )
                .values(is_orphaned=True, updated_at=datetime.now(timezone.utc))
            )

        # ── update store sync timestamp ───────────────────────────────────────
        await db.execute(
            update(Store)
            .where(Store.id == store.id)
            .values(last_sync_at=datetime.now(timezone.utc))
        )
        await db.commit()

    log.info(
        "Catalog sync: store=%s provider=%s total=%d archived=%d",
        store.id, store.provider, len(products),
        sum(1 for p in existing if p.is_archived),
    )
    return len(products)


async def sync_all_catalogs() -> dict[str, int]:
    """Синхронизирует каталоги всех активных магазинов всех пользователей."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Store, MarketplaceConnection)
            .join(MarketplaceConnection, Store.marketplace_connection_id == MarketplaceConnection.id)
            .where(Store.is_active.is_(True), MarketplaceConnection.is_active.is_(True))
        )
        pairs = result.all()

    summary: dict[str, int] = {}
    for store, conn in pairs:
        key = f"{store.provider}:{store.external_store_id}"
        try:
            count = await sync_store_catalog(store, conn)
            summary[key] = count
        except Exception as exc:
            log.error("Sync failed for %s: %s", key, exc)
            summary[key] = -1

    return summary
