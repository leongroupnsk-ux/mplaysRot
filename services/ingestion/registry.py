"""
Фабрика коннекторов — создаёт нужный коннектор по типу платформы/маркетплейса
на основе расшифрованных credentials из БД.
"""
from services.ingestion.base import BaseAdConnector, BaseMarketplaceConnector
from services.ingestion.connectors.yandex_direct.connector import YandexDirectConnector
from services.ingestion.connectors.vk_ads.connector import VKAdsConnector
from services.ingestion.connectors.vk_blogger.connector import VKBloggerConnector
from services.ingestion.connectors.telegram_ads.connector import TelegramAdsConnector
from services.ingestion.connectors.messenger_max.connector import MessengerMaxConnector
from services.ingestion.connectors.ozon.connector import OzonConnector
from services.ingestion.connectors.wildberries.connector import WildberriesConnector
from services.ingestion.connectors.yandex_market.connector import YandexMarketConnector
from services.ingestion.connectors.amazon.connector import AmazonConnector


def make_ad_connector(platform: str, credentials: dict) -> BaseAdConnector:
    match platform:
        case "yandex_direct":
            return YandexDirectConnector(
                access_token=credentials["access_token"],
                client_login=credentials["client_login"],
            )
        case "vk_ads":
            return VKAdsConnector(
                access_token=credentials["access_token"],
                account_id=credentials["account_id"],
            )
        case "vk_blogger":
            return VKBloggerConnector(
                access_token=credentials["access_token"],
                owner_ids=credentials.get("owner_ids", []),
            )
        case "telegram_ads":
            return TelegramAdsConnector(access_token=credentials["access_token"])
        case "messenger_max":
            return MessengerMaxConnector(
                access_token=credentials["access_token"],
                webhook_secret=credentials.get("webhook_secret", ""),
            )
        case _:
            raise ValueError(f"Unknown ad platform: {platform}")


def make_marketplace_connector(marketplace: str, credentials: dict) -> BaseMarketplaceConnector:
    match marketplace:
        case "ozon":
            return OzonConnector(
                client_id=credentials["client_id"],
                api_key=credentials["api_key"],
            )
        case "wildberries":
            return WildberriesConnector(api_key=credentials["api_key"])
        case "yandex_market":
            return YandexMarketConnector(
                oauth_token=credentials["oauth_token"],
                client_id=credentials["client_id"],
                campaign_id=credentials["campaign_id"],
            )
        case "amazon":
            return AmazonConnector(
                refresh_token=credentials["refresh_token"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                marketplace_id=credentials.get("marketplace_id", "ATVPDKIKX0DER"),
            )
        case _:
            raise ValueError(f"Unknown marketplace: {marketplace}")
