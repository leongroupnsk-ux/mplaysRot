from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import StoreProduct, VerificationFailLog
from app.models import MarketplaceType
from datetime import datetime


class SKUVerifier:
    """Verify that SKU belongs to the given store"""

    @staticmethod
    async def verify_sku(
        session: AsyncSession,
        user_id: int,
        store_id: int,
        external_product_id: str,
        marketplace: MarketplaceType,
        ip_address: str = None,
    ) -> tuple[bool, str]:
        """
        Verify that a product SKU belongs to the user's store.
        
        Args:
            session: AsyncSession for DB operations
            user_id: ID of user making the request
            store_id: Store ID to verify against
            external_product_id: SKU from marketplace
            marketplace: Marketplace type (WB, Ozon)
            ip_address: IP address for logging (optional)
            
        Returns:
            (is_verified: bool, reason: str)
            - (True, "") if verification passed
            - (False, reason) if verification failed
        """

        # Query: does this SKU exist for this store?
        stmt = select(StoreProduct).where(
            StoreProduct.store_id == store_id,
            StoreProduct.external_product_id == external_product_id,
            StoreProduct.marketplace == marketplace.value,
            StoreProduct.is_active == True,
            StoreProduct.deleted_at.is_(None),
        )

        result = await session.execute(stmt)
        product = result.scalars().first()

        # If product not found, log the attempt and return False
        if not product:
            # Log failed verification attempt
            fail_log = VerificationFailLog(
                user_id=user_id,
                store_id=store_id,
                external_product_id=external_product_id,
                marketplace=marketplace.value,
                reason="not_found",
                ip_address=ip_address or "unknown",
                timestamp=datetime.utcnow(),
            )
            session.add(fail_log)
            await session.commit()

            return False, f"Товар с артикулом {external_product_id} не найден в магазине. Проверьте правильность артикула или синхронизируйте каталог."

        # Check if product is marked as deleted
        if product.deleted_at is not None:
            fail_log = VerificationFailLog(
                user_id=user_id,
                store_id=store_id,
                external_product_id=external_product_id,
                marketplace=marketplace.value,
                reason="deleted",
                ip_address=ip_address or "unknown",
                timestamp=datetime.utcnow(),
            )
            session.add(fail_log)
            await session.commit()

            return False, f"Товар {external_product_id} был удалён из магазина."

        # Check if product is inactive
        if not product.is_active:
            fail_log = VerificationFailLog(
                user_id=user_id,
                store_id=store_id,
                external_product_id=external_product_id,
                marketplace=marketplace.value,
                reason="inactive",
                ip_address=ip_address or "unknown",
                timestamp=datetime.utcnow(),
            )
            session.add(fail_log)
            await session.commit()

            return False, f"Товар {external_product_id} временно недоступен."

        # Verification passed
        return True, ""

    @staticmethod
    async def bulk_verify_skus(
        session: AsyncSession,
        store_id: int,
        skus: list[tuple[str, MarketplaceType]],  # [(sku, marketplace), ...]
    ) -> dict:
        """
        Verify multiple SKUs at once.
        
        Returns dict: {(sku, marketplace): (is_verified, reason), ...}
        """
        results = {}

        for sku, marketplace in skus:
            stmt = select(StoreProduct).where(
                StoreProduct.store_id == store_id,
                StoreProduct.external_product_id == sku,
                StoreProduct.marketplace == marketplace.value,
                StoreProduct.is_active == True,
                StoreProduct.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            product = result.scalars().first()

            if product:
                results[(sku, marketplace.value)] = (True, "")
            else:
                results[(sku, marketplace.value)] = (False, "not_found")

        return results
