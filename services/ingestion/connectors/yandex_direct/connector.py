"""
Яндекс.Директ API v5.
Документация: https://yandex.ru/dev/direct/doc/reports/
"""
import json
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.ingestion.base import BaseAdConnector, AdStats

_REPORTS_URL = "https://api.direct.yandex.com/json/v5/reports"
_AUDIENCE_URL = "https://api.direct.yandex.com/json/v5/audiences"


class YandexDirectConnector(BaseAdConnector):
    platform = "yandex_direct"

    def __init__(self, access_token: str, client_login: str):
        self._token = access_token
        self._login = client_login

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Client-Login": self._login,
            "Accept-Language": "ru",
            "processingMode": "auto",
            "returnMoneyInMicros": "false",
            "skipReportHeader": "true",
            "skipColumnHeader": "false",
            "skipReportSummary": "true",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_stats(self, date_from: date, date_to: date) -> list[AdStats]:
        body = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from.isoformat(),
                    "DateTo": date_to.isoformat(),
                },
                "FieldNames": [
                    "Date", "CampaignId", "CampaignName",
                    "AdId", "AdGroupId",
                    "Impressions", "Clicks", "Cost",
                    "Ctr", "AvgCpc",
                    "Conversions", "Revenue",
                ],
                "ReportName": f"attribly_{date_from}_{date_to}",
                "ReportType": "AD_PERFORMANCE_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "NO",
            }
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                _REPORTS_URL,
                headers=self._headers(),
                content=json.dumps(body),
            )

        if response.status_code == 202:
            # Отчёт готовится асинхронно — повторяем (tenacity)
            raise RuntimeError("Report not ready yet (202), retrying")

        response.raise_for_status()
        return self._parse_tsv(response.text, date_from)

    def _parse_tsv(self, tsv: str, date_from: date) -> list[AdStats]:
        lines = tsv.strip().splitlines()
        if len(lines) < 2:
            return []

        headers = lines[0].split("\t")
        idx = {h: i for i, h in enumerate(headers)}
        result = []

        for line in lines[1:]:
            cols = line.split("\t")
            spend = float(cols[idx["Cost"]] or 0)
            clicks = int(cols[idx["Clicks"]] or 0)
            result.append(AdStats(
                stat_date=date.fromisoformat(cols[idx["Date"]]),
                ad_platform=self.platform,
                external_campaign_id=cols[idx["CampaignId"]],
                external_ad_id=cols[idx["AdId"]],
                ad_name=cols[idx["CampaignName"]],
                impressions=int(cols[idx["Impressions"]] or 0),
                clicks=clicks,
                spend=spend,
                ctr=float(cols[idx["Ctr"]] or 0),
                cpc=float(cols[idx["AvgCpc"]] or 0),
                conversions=int(cols[idx["Conversions"]] or 0),
                conversion_value=float(cols[idx["Revenue"]] or 0),
            ))

        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_audience(self, segment_id: str, identifiers: list[str]) -> str:
        """
        Создаёт сегмент в Яндекс.Аудиториях и возвращает его ID.
        identifiers — список хешей email (md5) или телефонов.
        """
        body = {
            "method": "add",
            "params": {
                "Audiences": [{
                    "Name": f"Attribly seed {segment_id}",
                    "Type": "HASHED_EMAIL",
                    "HashedEmails": identifiers,
                }]
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                _AUDIENCE_URL,
                headers={"Authorization": f"Bearer {self._token}"},
                json=body,
            )

        response.raise_for_status()
        data = response.json()
        return str(data["result"]["AddResults"][0]["Id"])

    async def test_connection(self) -> tuple[bool, str]:
        """Проверяет токен через лёгкий Campaigns.get с лимитом 1."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.direct.yandex.com/json/v5/campaigns",
                    headers=self._headers(),
                    json={"method": "get", "params": {"SelectionCriteria": {}, "FieldNames": ["Id"], "Page": {"Limit": 1}}},
                )
            body = resp.json()
            if resp.status_code == 401 or body.get("error", {}).get("error_code") == 53:
                return False, "Неверный OAuth-токен Яндекс.Директа"
            resp.raise_for_status()
            return True, "Подключение успешно"
        except Exception as exc:
            return False, f"Ошибка подключения: {exc}"
