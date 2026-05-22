import asyncio
import logging

from app.celery import celery

log = logging.getLogger(__name__)


@celery.task(name="app.tasks.catalog.sync_all_catalogs", bind=True, max_retries=2)
def sync_all_catalogs_task(self):
    """Синхронизирует каталоги всех активных магазинов (раз в 2 часа)."""
    try:
        from app.services.catalog import sync_all_catalogs
        summary = asyncio.get_event_loop().run_until_complete(sync_all_catalogs())
        total = sum(v for v in summary.values() if v >= 0)
        failed = [k for k, v in summary.items() if v < 0]
        log.info("Catalog sync done: %d products across %d stores", total, len(summary))
        if failed:
            log.warning("Catalog sync failed for stores: %s", failed)
        return {"total_products": total, "stores": len(summary), "failed": failed}
    except Exception as exc:
        log.error("Catalog sync task failed: %s", exc)
        raise self.retry(exc=exc, countdown=600)


@celery.task(name="app.tasks.catalog.sync_store_catalog")
def sync_store_catalog_task(store_id: str):
    """
    Запускает инкрементальную синхронизацию одного магазина.
    Вызывается при создании кампании если каталог устарел (>2 ч).
    """
    import asyncio
    from sqlalchemy import select
    from app.db.postgres import AsyncSessionLocal
    from app.models.catalog import Store
    from app.models.connections import MarketplaceConnection
    from app.services.catalog import sync_store_catalog

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Store, MarketplaceConnection)
                .join(MarketplaceConnection, Store.marketplace_connection_id == MarketplaceConnection.id)
                .where(Store.id == store_id)
            )
            row = result.one_or_none()
            if not row:
                log.warning("sync_store_catalog: store %s not found", store_id)
                return 0
            store, conn = row
        return await sync_store_catalog(store, conn)

    count = asyncio.get_event_loop().run_until_complete(_run())
    log.info("Single store sync %s: %d products", store_id, count)
    return {"store_id": store_id, "products": count}
