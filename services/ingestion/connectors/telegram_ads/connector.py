"""
Telegram Ads (TON Ad Platform).
Документация: https://ton.org/api (Ad Platform API)
Сбор статистики рекламных объявлений через официальный API.
"""
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.ingestion.base import BaseAdConnector, AdStats

_BASE_URL = "https://api.ton.org/v1"


class TelegramAdsConnector(BaseAdConnector):
    platform = "telegram_ads"

    def __init__(self, access_token: str):
        self._token = access_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        params = {
            "start_date": date_from.isoformat(),
            "end_date": date_to.isoformat(),
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # Получаем список объявлений
            ads_resp = await client.get(
                f"{_BASE_URL}/ads",
                headers=self._headers(),
                params=params,
            )
            ads_resp.raise_for_status()
            ads = ads_resp.json().get("ads", [])

            result: list[AdStats] = []
            for ad in ads:
                stat_resp = await client.get(
                    f"{_BASE_URL}/ads/{ad['id']}/stats",
                    headers=self._headers(),
                    params=params,
                )
                stat_resp.raise_for_status()
                stats = stat_resp.json()

                for day in stats.get("by_day", []):
                    spend = float(day.get("spent_ton", 0))
                    clicks = int(day.get("views", 0))  # Telegram Ads считает переходы как views с CTA
                    result.append(AdStats(
                        stat_date=date.fromisoformat(day["date"]),
                        ad_platform=self.platform,
                        external_campaign_id=str(ad.get("campaign_id", ad["id"])),
                        external_ad_id=str(ad["id"]),
                        ad_name=ad.get("title", ""),
                        impressions=int(day.get("impressions", 0)),
                        clicks=clicks,
                        spend=spend,
                        currency="TON",
                    ))
        return result

    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        """
        Telegram Ads не поддерживает загрузку пользовательских аудиторий
        через публичный API — таргетинг только по каналам/интересам.
        Используем обходной путь: возвращаем заглушку и логируем факт.
        """
        raise NotImplementedError(
            "Telegram Ads does not support custom audience upload via API. "
            "Use channel targeting as a proxy."
        )

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен Telegram Ads через список объявлений (лимит 1)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/ads",
                    headers={"Authorization": f"Bearer {self._token}"},
                    params={"limit": 1},
                )
            if resp.status_code in (401, 403):
                return False, "Неверный access_token Telegram Ads"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
