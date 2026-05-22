"""
Integration tests for /webhooks router.

ClickHouse client is mocked — no live infrastructure needed.
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.db.clickhouse import get_clickhouse
from app.main import app

NOW = datetime.now(timezone.utc).isoformat()


def _make_ch() -> MagicMock:
    ch = MagicMock()
    ch.insert = MagicMock()
    return ch


def _click_event(platform: str = "telegram_ads") -> dict:
    return {
        "type": "click",
        "event_id": str(uuid.uuid4()),
        "trax_id": "ABCDE12",
        "campaign_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "visitor_hash": "aabbcc",
        "ts": NOW,
        "ip_hash": "x" * 64,
        "device_type": "mobile",
        "os": "iOS",
        "browser": "Safari",
        "country": "RU",
        "region": "Москва",
        "referrer_domain": "t.me",
        "marketplace": "ozon",
    }


def _stat_event() -> dict:
    return {
        "type": "stats",
        "stat_date": "2024-01-15",
        "user_id": str(uuid.uuid4()),
        "campaign_id": str(uuid.uuid4()),
        "external_campaign_id": "ext-001",
        "external_ad_id": "ad-001",
        "ad_name": "Test Ad",
        "impressions": 1000,
        "clicks": 50,
        "spend": 2500.0,
        "currency": "RUB",
    }


# ── Telegram webhook ──────────────────────────────────────────────────────────

class TestTelegramWebhook:
    SECRET = "test-telegram-secret"

    @pytest.mark.asyncio
    async def test_accepts_click_event(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = self.SECRET
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/telegram",
                    json=[_click_event()],
                    headers={"X-Telegram-Secret": self.SECRET},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["accepted"] == 1

    @pytest.mark.asyncio
    async def test_accepts_stat_event(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = self.SECRET
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/telegram",
                    json=[_stat_event()],
                    headers={"X-Telegram-Secret": self.SECRET},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["accepted"] == 1

    @pytest.mark.asyncio
    async def test_wrong_secret_returns_403(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = self.SECRET
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/telegram",
                    json=[_click_event()],
                    headers={"X-Telegram-Secret": "wrong-secret"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_secret_in_settings_skips_auth(self):
        """Dev mode: when no secret is configured, all requests pass through."""
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = ""
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/telegram",
                    json=[_click_event()],
                    headers={"X-Telegram-Secret": "any-value"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_inserts_into_clickhouse(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = ""
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                await c.post(
                    "/webhooks/telegram",
                    json=[_click_event()],
                    headers={"X-Telegram-Secret": "any"},
                )

        app.dependency_overrides.clear()
        ch.insert.assert_called_once()
        call_args = ch.insert.call_args
        assert call_args[0][0] == "clicks"


# ── Messenger MAX webhook ─────────────────────────────────────────────────────

class TestMessengerMaxWebhook:
    SECRET = "test-max-secret"

    def _signature(self, body: bytes) -> str:
        return "sha256=" + hmac.new(
            self.SECRET.encode(), body, hashlib.sha256
        ).hexdigest()

    @pytest.mark.asyncio
    async def test_accepts_click_event_with_valid_signature(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch
        body = json.dumps([_click_event()]).encode()

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = ""
            mock_settings.messenger_max_webhook_secret = self.SECRET

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/messenger-max",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Max-Signature": self._signature(body),
                    },
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["accepted"] == 1

    @pytest.mark.asyncio
    async def test_wrong_signature_returns_403(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch
        body = json.dumps([_click_event()]).encode()

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = ""
            mock_settings.messenger_max_webhook_secret = self.SECRET

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/messenger-max",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Max-Signature": "sha256=badhash",
                    },
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_secret_skips_signature_check(self):
        ch = _make_ch()
        app.dependency_overrides[get_clickhouse] = lambda: ch
        body = json.dumps([_click_event()]).encode()

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.telegram_webhook_secret = ""
            mock_settings.messenger_max_webhook_secret = ""

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/webhooks/messenger-max",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Max-Signature": "sha256=anything",
                    },
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
