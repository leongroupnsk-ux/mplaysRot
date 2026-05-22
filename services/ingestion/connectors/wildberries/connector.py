"""
Wildberries Statistics API.
Документация: https://openapi.wildberries.ru/
"""
from datetime import date, datetime, timezone, timedelta

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from decimal import Decimal

from services.ingestion.base import BaseMarketplaceConnector, MarketplaceOrder, CatalogProduct, ConnectionError

_BASE_URL = "https://statistics-api.wildberries.ru/api/v1/supplier"


class WildberriesConnector(BaseMarketplaceConnector):
    marketplace = "wildberries"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _headers(self) -> dict:
        return {"Authorization": self._api_key}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_orders(self, date_from: date, date_to: date) -> list[MarketplaceOrder]:
        """
        WB отдаёт заказы от указанной даты до текущего момента (нет date_to).
        Фильтруем по date_to на нашей стороне.
        """
        params = {
            "dateFrom": datetime(date_from.year, date_from.month, date_from.day,
                                 tzinfo=timezone.utc).isoformat(),
            "flag": 0,  # 0 = все заказы включая отменённые
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{_BASE_URL}/orders",
                headers=self._headers(),
                params=params,
            )

        response.raise_for_status()
        orders_raw = response.json()

        result: list[MarketplaceOrder] = []
        cutoff = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc)

        for order in orders_raw:
            ordered_at_str = order.get("date", "")
            if not ordered_at_str:
                continue

            ordered_at = datetime.fromisoformat(ordered_at_str.replace("Z", "+00:00"))
            if ordered_at > cutoff:
                continue

            result.append(MarketplaceOrder(
                order_id=str(order["gNumber"]),
                marketplace=self.marketplace,
                product_id=str(order.get("supplierArticle", "")),
                sku=str(order.get("nmId", "")),
                quantity=1,  # WB всегда 1 единица на строку заказа
                order_amount=float(order.get("totalPrice", 0)),
                currency="RUB",
                order_status="cancelled" if order.get("isCancel") else "confirmed",
                ordered_at=ordered_at.isoformat(),
            ))

        return result

    async def test_connection(self) -> tuple[bool, str]:
        """
        Проверяет API-ключ WB.
        Последовательно пробует несколько эндпоинтов — у продавцов бывают
        ключи только со скоупом Статистика или только Маркетплейс.
        Считаем ключ валидным, если хотя бы один эндпоинт вернул не 401/403.
        """
        endpoints = [
            # Seller Info — работает с любым ключом (единый токен WB 2024)
            ("GET", "https://common-api.wildberries.ru/api/v1/seller-info"),
            # Marketplace API v3
            ("GET", "https://marketplace-api.wildberries.ru/api/v3/warehouses"),
            # Statistics API — старые ключи
            ("GET", "https://statistics-api.wildberries.ru/api/v1/supplier/orders"
                    "?dateFrom=2024-01-01T00%3A00%3A00&flag=0"),
        ]
        last_error = "Неверный API-ключ Wildberries"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for method, url in endpoints:
                    try:
                        resp = await client.request(method, url, headers=self._headers())
                        if resp.status_code == 401:
                            last_error = "Неверный API-ключ Wildberries (401)"
                            continue  # попробуем следующий
                        # 200, 403 (скоуп не тот, но ключ валиден), 404 — всё ок
                        return True, "Подключение успешно"
                    except httpx.TimeoutException:
                        last_error = "Таймаут подключения к Wildberries API"
                        continue
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
        return False, last_error

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_products(self, limit: int = 1000) -> list[CatalogProduct]:
        """
        Получить каталог WB через Content API.
        Корневой артикул — nmID; вариации — sizes[].chrtID с отдельным артикулом.
        """
        result: list[CatalogProduct] = []
        cursor: dict = {}
        content_url = "https://content-api.wildberries.ru/content/v2/get/cards/list"

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                payload = {
                    "settings": {
                        "cursor": {**cursor, "limit": min(limit, 100)},
                        "filter": {"withPhoto": -1},
                    }
                }
                resp = await client.post(
                    content_url,
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                cards = data.get("cards", [])
                if not cards:
                    break

                for card in cards:
                    nm_id = str(card.get("nmID", ""))
                    sizes = card.get("sizes", [])
                    # Суммарный сток по всем размерам
                    total_stock = sum(
                        sum(wh.get("wh", 0) for wh in sz.get("stocks", []))
                        for sz in sizes
                    )
                    image_url = (card.get("photos") or [{}])[0].get("big", "")
                    has_variations = len(sizes) > 1
                    price_raw = card.get("sizes", [{}])[0].get("price", {})
                    price = Decimal(str(price_raw.get("total", 0))) / 100

                    result.append(CatalogProduct(
                        external_product_id=nm_id,
                        title=card.get("title", ""),
                        price=price,
                        stock=total_stock,
                        image_url=image_url,
                        has_variations=has_variations,
                    ))
                    # Размерные вариации
                    for sz in sizes:
                        chrt_id = str(sz.get("chrtID", ""))
                        if chrt_id and chrt_id != nm_id:
                            sz_stock = sum(wh.get("wh", 0) for wh in sz.get("stocks", []))
                            sz_price = Decimal(str(sz.get("price", {}).get("total", 0))) / 100
                            result.append(CatalogProduct(
                                external_product_id=chrt_id,
                                title=f"{card.get('title', '')} ({sz.get('techSize', '')})",
                                price=sz_price,
                                stock=sz_stock,
                                parent_external_id=nm_id,
                                has_variations=False,
                            ))

                cursor_data = data.get("cursor", {})
                if cursor_data.get("total", 0) < min(limit, 100):
                    break
                cursor = {
                    "updatedAt": cursor_data.get("updatedAt", ""),
                    "nmID": cursor_data.get("nmID", 0),
                }

        return result
