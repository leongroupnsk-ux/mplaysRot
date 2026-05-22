"""
Messenger MAX API.
Получает события покупок и рекламные метрики через API платформы.
"""
from datetime import date
import hashlib

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.ingestion.base import BaseAdConnector, AdStats

_BASE_URL = "https://api.messenger.com/v1"


class MessengerMaxConnector(BaseAdConnector):
    platform = "messenger_max"

    def __init__(self, access_token: str, webhook_secret: str):
        self._token = access_token
        self._webhook_secret = webhook_secret

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "metrics": "impressions,clicks,spend,ctr",
            "breakdown": "day,ad_id",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{_BASE_URL}/ads/stats",
                headers=self._headers(),
                params=params,
            )
        response.raise_for_status()
        return self._parse(response.json())

    def _parse(self, data: dict) -> list[AdStats]:
        result = []
        for row in data.get("data", []):
            spend = float(row.get("spend", 0))
            clicks = int(row.get("clicks", 0))
            result.append(AdStats(
                stat_date=date.fromisoformat(row["date"]),
                ad_platform=self.platform,
                external_campaign_id=str(row.get("campaign_id", "")),
                external_ad_id=str(row["ad_id"]),
                ad_name=row.get("ad_name", ""),
                impressions=int(row.get("impressions", 0)),
                clicks=clicks,
                spend=spend,
                ctr=float(row.get("ctr", 0)),
                cpc=spend / clicks if clicks else 0.0,
            ))
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        """Синхронизирует сегмент пользователей по MAX User ID."""
        payload = {
            "name": f"Attribly seed {segment_id}",
            "type": "CUSTOM",
            "user_ids": identifiers,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{_BASE_URL}/audiences",
                headers=self._headers(),
                json=payload,
            )
        response.raise_for_status()
        return str(response.json()["audience_id"])

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """HMAC-SHA256 верификация подписи входящего вебхука."""
        expected = hashlib.sha256(self._webhook_secret.encode() + payload).hexdigest()
        return hashlib.compare_digest(expected, signature)

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен Messenger MAX через /me."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_BASE_URL}/me",
                    headers=self._headers(),
                )
            if resp.status_code in (401, 403):
                return False, "Неверный access_token Messenger MAX"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
