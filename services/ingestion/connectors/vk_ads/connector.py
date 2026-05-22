"""
VK Ads API.
Документация: https://ads.vk.com/api/v3/
"""
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.ingestion.base import BaseAdConnector, AdStats

_BASE_URL = "https://ads.vk.com/api/v3"


class VKAdsConnector(BaseAdConnector):
    platform = "vk_ads"

    def __init__(self, access_token: str, account_id: str):
        self._token = access_token
        self._account_id = account_id

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        params = {
            "account_id": self._account_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "fields": "id,name,impressions,clicks,spent,ctr,ecpc",
            "level": "ad",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{_BASE_URL}/statistics/ads/day.json",
                headers=self._headers(),
                params=params,
            )

        response.raise_for_status()
        return self._parse(response.json(), date_from, date_to)

    def _parse(self, data: dict, date_from: date, date_to: date) -> list[AdStats]:
        result = []
        for item in data.get("response", {}).get("items", []):
            for day_stat in item.get("stats", []):
                spend = float(day_stat.get("spent", 0))
                clicks = int(day_stat.get("clicks", 0))
                impressions = int(day_stat.get("impressions", 0))
                result.append(AdStats(
                    stat_date=date.fromisoformat(day_stat["day"]),
                    ad_platform=self.platform,
                    external_campaign_id=str(item.get("campaign_id", "")),
                    external_ad_id=str(item["id"]),
                    ad_name=item.get("name", ""),
                    impressions=impressions,
                    clicks=clicks,
                    spend=spend,
                    ctr=float(day_stat.get("ctr", 0)),
                    cpc=float(day_stat.get("ecpc", 0)),
                ))
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        """
        Создаёт ретаргетинговую аудиторию по хешам.
        identifiers — md5-хеши email или телефонов.
        """
        payload = {
            "account_id": self._account_id,
            "name": f"Attribly seed {segment_id}",
            "is_retargeting": 1,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Создаём аудиторию
            resp = await client.post(
                f"{_BASE_URL}/retargeting.json",
                headers=self._headers(),
                data=payload,
            )
            resp.raise_for_status()
            audience_id = resp.json()["response"]["id"]

            # 2. Загружаем хеши
            upload_resp = await client.post(
                f"{_BASE_URL}/retargeting/contacts.json",
                headers=self._headers(),
                data={
                    "account_id": self._account_id,
                    "target_group_id": audience_id,
                    "contacts": "\n".join(identifiers),
                },
            )
            upload_resp.raise_for_status()

        return str(audience_id)

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен VK Ads через список кабинетов."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/agencies/clients.json",
                    headers=self._headers(),
                    params={"account_id": self._account_id, "limit": 1},
                )
            if resp.status_code in (401, 403):
                return False, "Неверный access_token VK Ads"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
