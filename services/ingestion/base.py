"""Базовый класс для всех коннекторов."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class AdStats:
    stat_date: date
    ad_platform: str
    external_campaign_id: str
    external_ad_id: str
    ad_name: str
    impressions: int
    clicks: int
    spend: float
    currency: str = "RUB"
    ctr: float = 0.0
    cpc: float = 0.0
    conversions: int = 0
    conversion_value: float = 0.0


@dataclass
class MarketplaceOrder:
    order_id: str
    marketplace: str
    product_id: str
    sku: str
    quantity: int
    order_amount: float
    currency: str
    order_status: str
    ordered_at: str   # ISO-8601
    delivered_at: str = ""
    utm_trax_id: str = ""   # trax_id из UTM-параметров (Ozon, Яндекс.Маркет)


@dataclass
class CatalogProduct:
    """Товар из каталога маркетплейса."""
    external_product_id: str       # nmID (WB) / offer_id (Ozon) / offerId (YM) / ASIN (Amazon)
    title: str
    price: Decimal
    stock: int
    parent_external_id: str = ""   # пусто для корневых; заполнен для вариаций
    image_url: str = ""
    has_variations: bool = False


class ConnectionError(Exception):
    """Raised when test_connection() fails (auth error, network, etc.)."""


class BaseAdConnector(ABC):
    platform: str

    @abstractmethod
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        """Получить статистику по всем кампаниям за период."""

    @abstractmethod
    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        """Загрузить seed-аудиторию в кабинет. Возвращает external_segment_id."""

    async def test_connection(self) -> tuple[bool, str]:
        """Проверить валидность токена. Возвращает (ok, message)."""
        raise NotImplementedError


class BaseMarketplaceConnector(ABC):
    marketplace: str

    @abstractmethod
    async def fetch_orders(self, date_from: date, date_to: date) -> list[MarketplaceOrder]:
        """Получить список заказов за период."""

    @abstractmethod
    async def fetch_products(self, limit: int = 1000) -> list[CatalogProduct]:
        """Получить каталог товаров с остатками и вариациями."""

    async def test_connection(self) -> tuple[bool, str]:
        """Проверить валидность ключей. Возвращает (ok, message)."""
        raise NotImplementedError
