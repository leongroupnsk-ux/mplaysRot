"""
Amazon Selling Partner API (SP-API) + Amazon Ads API.
Документация: https://developer-docs.amazon.com/sp-api/
"""
import hashlib
import hmac
import json
from datetime import date, datetime, timezone
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from decimal import Decimal

from services.ingestion.base import BaseMarketplaceConnector, MarketplaceOrder, CatalogProduct, ConnectionError

_SP_API_BASE = "https://sellingpartnerapi-eu.amazon.com"
_LWA_URL = "https://api.amazon.com/auth/o2/token"

_STATUS_MAP = {
    "Pending": "confirmed",
    "Unshipped": "confirmed",
    "PartiallyShipped": "confirmed",
    "Shipped": "delivered",
    "Canceled": "cancelled",
    "Unfulfillable": "cancelled",
}


class AmazonConnector(BaseMarketplaceConnector):
    marketplace = "amazon"

    def __init__(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        marketplace_id: str = "ATVPDKIKX0DER",
    ):
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._marketplace_id = marketplace_id
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """LWA (Login with Amazon) обмен refresh_token на access_token."""
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                _LWA_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_orders(self, date_from: date, date_to: date) -> list[MarketplaceOrder]:
        token = await self._get_access_token()
        result: list[MarketplaceOrder] = []
        next_token: str | None = None

        headers = {
            "x-amz-access-token": token,
            "x-amz-date": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                params: dict = {
                    "MarketplaceIds": self._marketplace_id,
                    "CreatedAfter": datetime(date_from.year, date_from.month, date_from.day,
                                            tzinfo=timezone.utc).isoformat(),
                    "CreatedBefore": datetime(date_to.year, date_to.month, date_to.day,
                                             23, 59, 59, tzinfo=timezone.utc).isoformat(),
                    "MaxResultsPerPage": 100,
                }
                if next_token:
                    params = {"NextToken": next_token}

                response = await client.get(
                    f"{_SP_API_BASE}/orders/v0/orders",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json().get("payload", {})
                orders = data.get("Orders", [])

                for order in orders:
                    items = await self._fetch_order_items(client, headers, order["AmazonOrderId"])
                    status = _STATUS_MAP.get(order.get("OrderStatus", ""), order.get("OrderStatus", ""))

                    for item in items:
                        result.append(MarketplaceOrder(
                            order_id=order["AmazonOrderId"],
                            marketplace=self.marketplace,
                            product_id=item.get("SellerSKU", ""),
                            sku=item.get("ASIN", ""),
                            quantity=int(item.get("QuantityOrdered", 1)),
                            order_amount=float(
                                item.get("ItemPrice", {}).get("Amount", 0)
                            ),
                            currency=item.get("ItemPrice", {}).get("CurrencyCode", "USD"),
                            order_status=status,
                            ordered_at=order.get("PurchaseDate", ""),
                        ))

                next_token = data.get("NextToken")
                if not next_token:
                    break

        return result

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет LWA-токен через получение access_token."""
        try:
            await self._get_access_token()
            return True, "Подключение успешно"
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (400, 401):
                return False, "Неверный refresh_token, client_id или client_secret Amazon"
            return False, f"Ошибка Amazon LWA: {exc}"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_products(self, limit: int = 1000) -> list[CatalogProduct]:
        """
        Получить каталог Amazon через Catalog Items API v2022-04-01.
        parentASIN → childASINs — стандартная иерархия вариаций Amazon.
        """
        token = await self._get_access_token()
        headers = {
            "x-amz-access-token": token,
            "x-amz-date": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "Content-Type": "application/json",
        }
        result: list[CatalogProduct] = []
        next_token: str | None = None

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                params: dict = {
                    "marketplaceIds": self._marketplace_id,
                    "includedData": "summaries,attributes,relationships",
                    "pageSize": min(limit, 20),
                }
                if next_token:
                    params["pageToken"] = next_token

                resp = await client.get(
                    f"{_SP_API_BASE}/catalog/2022-04-01/items",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])

                for item in items:
                    asin = item.get("asin", "")
                    summaries = (item.get("summaries") or [{}])[0]
                    rels = item.get("relationships", {}).get("relationships", [])
                    parent_asin = next(
                        (r["childAsins"][0] for r in rels if r.get("type") == "VARIATION" and r.get("parentAsin")),
                        ""
                    ) if rels else ""
                    # Фактически parentAsin лежит в relationships[type=VARIATION].parentAsin
                    for rel in rels:
                        if rel.get("type") == "VARIATION" and rel.get("parentAsin"):
                            parent_asin = rel["parentAsin"]
                            break

                    price_amount = (
                        item.get("attributes", {})
                        .get("list_price", [{}])[0]
                        .get("value", 0)
                    )
                    stock = (
                        item.get("attributes", {})
                        .get("number_of_items", [{}])[0]
                        .get("value", 0)
                    )
                    image_url = summaries.get("mainImage", {}).get("link", "")
                    child_asins = [
                        r.get("childAsins", [])
                        for r in rels if r.get("type") == "VARIATION"
                    ]
                    has_variations = bool(child_asins and child_asins[0])

                    result.append(CatalogProduct(
                        external_product_id=asin,
                        title=summaries.get("itemName", ""),
                        price=Decimal(str(price_amount)),
                        stock=stock,
                        parent_external_id=parent_asin,
                        image_url=image_url,
                        has_variations=has_variations,
                    ))

                next_token = data.get("pagination", {}).get("nextToken")
                if not next_token:
                    break

        return result

    async def _fetch_order_items(
        self, client: httpx.AsyncClient, headers: dict, order_id: str
    ) -> list[dict]:
        response = await client.get(
            f"{_SP_API_BASE}/orders/v0/orders/{order_id}/orderItems",
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("payload", {}).get("OrderItems", [])
