"""
VK Blogger / VK API для сообществ.
Получает метрики публикаций с трекинг-ссылками Attribly.
"""
from datetime import date, datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.ingestion.base import BaseAdConnector, AdStats

_VK_API_URL = "https://api.vk.com/method"
_VK_API_VERSION = "5.199"


class VKBloggerConnector(BaseAdConnector):
    """
    Для VK-блогеров нет отдельного рекламного кабинета — мы отслеживаем
    переходы через трекинг-ссылки и получаем охваты постов через VK API.
    upload_audience не применимо для этого канала.
    """
    platform = "vk_blogger"

    def __init__(self, access_token: str, owner_ids: list[str]):
        self._token = access_token
        self._owner_ids = owner_ids  # ID групп/пользователей блогеров

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        stats: list[AdStats] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for owner_id in self._owner_ids:
                posts = await self._fetch_posts(client, owner_id, date_from, date_to)
                for post in posts:
                    stats.append(AdStats(
                        stat_date=datetime.fromtimestamp(
                            post["date"], tz=timezone.utc
                        ).date(),
                        ad_platform=self.platform,
                        external_campaign_id=str(owner_id),
                        external_ad_id=str(post["id"]),
                        ad_name=post.get("text", "")[:80],
                        impressions=post.get("views", {}).get("count", 0),
                        clicks=post.get("reposts", {}).get("count", 0),
                        spend=0.0,  # стоимость поста вносится вручную
                    ))
        return stats

    async def _fetch_posts(
        self, client: httpx.AsyncClient, owner_id: str, date_from: date, date_to: date
    ) -> list[dict]:
        ts_from = int(datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc).timestamp())
        ts_to = int(datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

        response = await client.get(
            f"{_VK_API_URL}/wall.get",
            params={
                "owner_id": owner_id,
                "count": 100,
                "filter": "owner",
                "access_token": self._token,
                "v": _VK_API_VERSION,
            },
        )
        response.raise_for_status()
        items = response.json().get("response", {}).get("items", [])
        return [p for p in items if ts_from <= p.get("date", 0) <= ts_to]

    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        # VK Blogger — канал для размещений, не для ретаргетинга
        raise NotImplementedError("VK Blogger does not support audience upload")

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен VK Blogger через users.get."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{_VK_API_URL}/users.get",
                    params={"access_token": self._token, "v": _VK_API_VERSION},
                )
            data = resp.json()
            if "error" in data:
                code = data["error"].get("error_code")
                if code in (5, 15):
                    return False, "Неверный access_token VK"
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
