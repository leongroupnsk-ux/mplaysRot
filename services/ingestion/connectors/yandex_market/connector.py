"""
Яндекс.Маркет API (партнёрский).
Документация: https://yandex.ru/dev/market/partner-api/
"""
import re
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from decimal import Decimal

from services.ingestion.base import BaseMarketplaceConnector, MarketplaceOrder, CatalogProduct, ConnectionError

_TRAX_RE = re.compile(r"(?:^|[?&])trax_id=([a-z0-9]{8})(?:&|$)")

_BASE_URL = "https://api.partner.market.yandex.ru/v2"

_STATUS_MAP = {
    "PROCESSING": "confirmed",
    "DELIVERY": "confirmed",
    "DELIVERED": "delivered",
    "CANCELLED": "cancelled",
    "CANCELLED_IN_DELIVERY": "cancelled",
}


class YandexMarketConnector(BaseMarketplaceConnector):
    marketplace = "yandex_market"

    def __init__(self, oauth_token: str, client_id: str, campaign_id: str):
        self._token = oauth_token
        self._client_id = client_id
        self._campaign_id = campaign_id

    def _headers(self) -> dict:
        return {
            "Authorization": f"OAuth oauth_token={self._token}, oauth_client_id={self._client_id}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_orders(self, date_from: date, date_to: date) -> list[MarketplaceOrder]:
        result: list[MarketplaceOrder] = []
        page = 1

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                params = {
                    "fromDate": date_from.strftime("%d-%m-%Y"),
                    "toDate": date_to.strftime("%d-%m-%Y"),
                    "page": page,
                    "pageSize": 200,
                }

                response = await client.get(
                    f"{_BASE_URL}/campaigns/{self._campaign_id}/orders",
                    headers=self._headers(),
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                orders = data.get("orders", [])

                if not orders:
                    break

                for order in orders:
                    status = _STATUS_MAP.get(order.get("status", ""), order.get("status", ""))
                    trax_id = _extract_trax_id(order)
                    for item in order.get("items", []):
                        result.append(MarketplaceOrder(
                            order_id=str(order["id"]),
                            marketplace=self.marketplace,
                            product_id=str(item.get("offerId", "")),
                            sku=str(item.get("shopSku", "")),
                            quantity=item.get("count", 1),
                            order_amount=float(item.get("price", 0)) * item.get("count", 1),
                            currency="RUB",
                            order_status=status,
                            ordered_at=order.get("creationDate", ""),
                            utm_trax_id=trax_id,
                        ))

                pager = data.get("pager", {})
                if page >= pager.get("pagesCount", 1):
                    break
                page += 1

        return result


    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен через /campaigns/{id}/settings."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/campaigns/{self._campaign_id}/settings",
                    headers=self._headers(),
                )
            if resp.status_code in (401, 403):
                return False, "Неверный OAuth-токен или Client-Id Яндекс.Маркета"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_products(self, limit: int = 1000) -> list[CatalogProduct]:
        """
        Получить каталог YM через offer-mapping-entries.
        Вариации группируются через marketModelId.
        """
        result: list[CatalogProduct] = []
        page_token: str | None = None
        seen_models: dict[str, str] = {}  # model_id → parent offerId

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                params: dict = {"limit": min(limit, 200)}
                if page_token:
                    params["page_token"] = page_token

                resp = await client.get(
                    f"{_BASE_URL}/businesses/{self._campaign_id}/offer-mappings",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json().get("result", {})
                entries = data.get("offerMappings", [])
                if not entries:
                    break

                for entry in entries:
                    offer = entry.get("offer", {})
                    offer_id = offer.get("offerId", "")
                    market_sku = entry.get("mapping", {}).get("marketSku", "")
                    model_id = str(entry.get("mapping", {}).get("marketModelId", ""))
                    price = Decimal(str(offer.get("price", 0)))
                    stock = offer.get("stockQuantity", 0)
                    image_url = (offer.get("pictures") or [""])[0]
                    title = offer.get("name", "")

                    parent_id = ""
                    if model_id:
                        if model_id in seen_models:
                            parent_id = seen_models[model_id]
                        else:
                            seen_models[model_id] = offer_id

                    result.append(CatalogProduct(
                        external_product_id=offer_id,
                        title=title,
                        price=price,
                        stock=stock,
                        parent_external_id=parent_id,
                        image_url=image_url,
                        has_variations=bool(model_id and parent_id == ""),
                    ))

                page_token = data.get("paging", {}).get("nextPageToken")
                if not page_token:
                    break

        return result


def _extract_trax_id(order: dict) -> str:
    """Ищет trax_id в UTM-полях заказа YM (buyer.utmSource, context, customFields)."""
    # YM v2 отдаёт контекст трафика в поле 'context' или 'buyer'
    for path in (
        ("context", "utmTerm"),
        ("context", "utmContent"),
        ("buyer", "utmTerm"),
        ("customFields",),
    ):
        node = order
        for key in path:
            if not isinstance(node, dict):
                break
            node = node.get(key, {})
        value = node if isinstance(node, str) else ""
        if value:
            m = _TRAX_RE.search(f"?{value}" if "=" in value and "?" not in value else value)
            if m:
                return m.group(1)
    return ""
