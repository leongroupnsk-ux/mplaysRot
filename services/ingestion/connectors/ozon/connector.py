"""
Ozon Seller API v3 + Performance API.
Документация: https://docs.ozon.ru/api/seller/
"""
import re
from datetime import date, datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from decimal import Decimal

from services.ingestion.base import BaseMarketplaceConnector, MarketplaceOrder, CatalogProduct, ConnectionError

# trax_id = 8 строчных букв/цифр
_TRAX_RE = re.compile(r"(?:^|[?&])trax_id=([a-z0-9]{8})(?:&|$)")

_BASE_URL = "https://api-seller.ozon.ru"


class OzonConnector(BaseMarketplaceConnector):
    marketplace = "ozon"

    def __init__(self, client_id: str, api_key: str):
        self._client_id = client_id
        self._api_key = api_key

    def _headers(self) -> dict:
        return {
            "Client-Id": self._client_id,
            "Api-Key": self._api_key,
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_orders(self, date_from: date, date_to: date) -> list[MarketplaceOrder]:
        result: list[MarketplaceOrder] = []
        offset = 0
        limit = 1000

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                payload = {
                    "dir": "ASC",
                    "filter": {
                        "since": _to_rfc3339(date_from),
                        "to": _to_rfc3339(date_to, end_of_day=True),
                        "status": "",
                    },
                    "limit": limit,
                    "offset": offset,
                    "with": {
                        "analytics_data": True,
                        "financial_data": True,
                    },
                }

                response = await client.post(
                    f"{_BASE_URL}/v3/posting/fbo/list",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                postings = data.get("result", {}).get("postings", [])

                if not postings:
                    break

                for posting in postings:
                    trax_id = _extract_trax_id(posting.get("analytics_data", {}))
                    for product in posting.get("products", []):
                        result.append(MarketplaceOrder(
                            order_id=posting["posting_number"],
                            marketplace=self.marketplace,
                            product_id=str(product["offer_id"]),
                            sku=str(product["sku"]),
                            quantity=product["quantity"],
                            order_amount=float(product["price"]) * product["quantity"],
                            currency="RUB",
                            order_status=posting["status"],
                            ordered_at=posting["in_process_at"],
                            delivered_at=posting.get("delivering_date", ""),
                            utm_trax_id=trax_id,
                        ))

                if len(postings) < limit:
                    break
                offset += limit

        return result


    async def test_connection(self) -> tuple[bool, str]:
        """Лёгкий запрос к Ozon API для проверки ключей."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{_BASE_URL}/v1/warehouse/list",
                    headers=self._headers(),
                    json={},
                )
            if resp.status_code == 401:
                return False, "Неверный Client-Id или Api-Key"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_products(self, limit: int = 1000) -> list[CatalogProduct]:
        """Получить каталог Ozon с остатками и вариациями (offer_id/product_id)."""
        result: list[CatalogProduct] = []
        last_id = ""

        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                payload = {
                    "filter": {"visibility": "ALL"},
                    "last_id": last_id,
                    "limit": min(limit, 1000),
                }
                resp = await client.post(
                    f"{_BASE_URL}/v2/product/list",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json().get("result", {})
                items = data.get("items", [])
                if not items:
                    break

                # Запрашиваем детали (цена, сток, вариации) батчем
                product_ids = [str(it["product_id"]) for it in items]
                detail_resp = await client.post(
                    f"{_BASE_URL}/v2/product/info/list",
                    headers=self._headers(),
                    json={"product_id": product_ids},
                )
                detail_resp.raise_for_status()
                details = {
                    str(d["id"]): d
                    for d in detail_resp.json().get("result", {}).get("items", [])
                }

                for it in items:
                    pid = str(it["product_id"])
                    d = details.get(pid, {})
                    # Ozon: размерные сетки хранятся в d["sources"] — каждый источник дочерний
                    sources = d.get("sources", [])
                    has_variations = len(sources) > 1
                    stock = sum(
                        s.get("stock", 0) for s in d.get("stocks", {}).get("stocks", [])
                    )
                    result.append(CatalogProduct(
                        external_product_id=it.get("offer_id", pid),
                        title=d.get("name", ""),
                        price=Decimal(str(d.get("price", "0"))),
                        stock=stock,
                        image_url=(d.get("images") or [{}])[0].get("file_name", ""),
                        has_variations=has_variations,
                    ))
                    # Дочерние вариации (sources)
                    for src in sources:
                        if src.get("sku") != it.get("offer_id"):
                            result.append(CatalogProduct(
                                external_product_id=src["sku"],
                                title=d.get("name", ""),
                                price=Decimal(str(d.get("price", "0"))),
                                stock=src.get("stock", 0),
                                parent_external_id=it.get("offer_id", pid),
                                has_variations=False,
                            ))

                last_id = data.get("last_id", "")
                if not last_id or len(items) < min(limit, 1000):
                    break

        return result


def _extract_trax_id(analytics_data: dict) -> str:
    """Ищет trax_id в UTM-полях analytics_data заказа Ozon."""
    # Ozon может вернуть utm_term или custom_params со строкой trax_id=XXXXXXXX
    for field in ("utm_term", "utm_content", "utm_campaign", "custom_params", "visit_parameters"):
        value = analytics_data.get(field, "")
        if not isinstance(value, str):
            continue
        m = _TRAX_RE.search(f"?{value}" if "=" in value and "?" not in value else value)
        if m:
            return m.group(1)
    return ""


def _to_rfc3339(d: date, end_of_day: bool = False) -> str:
    if end_of_day:
        return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc).isoformat()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat()
