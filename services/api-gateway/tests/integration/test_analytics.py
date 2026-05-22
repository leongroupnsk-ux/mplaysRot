"""
Integration tests for /analytics and /attribution routers.

ClickHouse client is mocked — no live infrastructure needed.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.db.clickhouse import get_clickhouse
from app.main import app
from app.utils.jwt import create_access_token
from tests.conftest import make_user, make_mock_db

NOW = datetime.now(timezone.utc)
DATE_FROM = "2024-01-01"
DATE_TO = "2024-01-31"


def _auth_headers(user_id) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _make_ch_mock(result_rows: list) -> MagicMock:
    ch = MagicMock()
    query_result = MagicMock()
    query_result.result_rows = result_rows
    ch.query.return_value = query_result
    return ch


@pytest.fixture
def user():
    return make_user()


@pytest.fixture
def mock_db():
    return make_mock_db()


def _db_returning_user(user):
    db = make_mock_db()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    return db


# ── /analytics/overview ───────────────────────────────────────────────────────

class TestOverview:
    def test_returns_200_with_data(self, client_factory, user):
        ch = _make_ch_mock([(50000.0, 150000.0, 12, 340)])
        self._run(user, ch, DATE_FROM, DATE_TO, expected_status=200)

    def test_empty_table_returns_zeros(self, client_factory, user):
        ch = _make_ch_mock([(None, None, None, None)])
        body = self._run(user, ch, DATE_FROM, DATE_TO, expected_status=200)
        assert body["total_spend"] == 0.0
        assert body["roas"] == 0.0
        assert body["attributed_orders"] == 0

    def test_roas_calculated(self, client_factory, user):
        ch = _make_ch_mock([(10000.0, 40000.0, 5, 100)])
        body = self._run(user, ch, DATE_FROM, DATE_TO, expected_status=200)
        assert body["roas"] == pytest.approx(4.0)

    def test_missing_dates_returns_422(self, client_factory, user):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        db = _db_returning_user(user)
        ch = _make_ch_mock([])
        app.dependency_overrides[get_clickhouse] = lambda: ch
        from app.db.postgres import get_db
        app.dependency_overrides[get_db] = lambda: db

        async def _run():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get(
                    "/v1/analytics/overview",
                    headers=_auth_headers(user.id),
                )

        resp = asyncio.get_event_loop().run_until_complete(_run())
        app.dependency_overrides.clear()
        assert resp.status_code == 422

    def test_marketplace_filter_passed_to_query(self, client_factory, user):
        ch = _make_ch_mock([(5000.0, 20000.0, 3, 80)])
        self._run(user, ch, DATE_FROM, DATE_TO, extra="&marketplace=ozon", expected_status=200)
        call_args = ch.query.call_args
        assert "mp" in call_args[1]["parameters"]

    def _run(self, user, ch, date_from, date_to, extra="", expected_status=200):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from app.db.postgres import get_db

        db = _db_returning_user(user)
        app.dependency_overrides[get_clickhouse] = lambda: ch
        app.dependency_overrides[get_db] = lambda: db

        async def _go():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get(
                    f"/v1/analytics/overview?date_from={date_from}&date_to={date_to}{extra}",
                    headers=_auth_headers(user.id),
                )

        resp = asyncio.get_event_loop().run_until_complete(_go())
        app.dependency_overrides.clear()
        assert resp.status_code == expected_status
        return resp.json()


# ── /analytics/funnel ─────────────────────────────────────────────────────────

class TestFunnel:
    CAMPAIGN_ID = str(uuid.uuid4())

    def test_returns_4_steps(self, user):
        ch = _make_ch_mock([(100, 30, 20, 5)])
        body = self._run(user, ch)
        assert len(body["steps"]) == 4
        assert body["steps"][0]["name"] == "Клики"
        assert body["steps"][3]["name"] == "Заказы"

    def test_conversion_rates(self, user):
        ch = _make_ch_mock([(100, 40, 20, 10)])
        body = self._run(user, ch)
        steps = {s["name"]: s for s in body["steps"]}
        assert steps["Избранное"]["conversion_rate"] == pytest.approx(0.4)
        assert steps["Корзина"]["conversion_rate"] == pytest.approx(0.2)
        assert steps["Заказы"]["conversion_rate"] == pytest.approx(0.1)

    def test_zero_clicks_no_division_error(self, user):
        ch = _make_ch_mock([(0, 0, 0, 0)])
        body = self._run(user, ch)
        # first step CR is always 1.0 (baseline); downstream steps must be 0.0
        for step in body["steps"][1:]:
            assert step["conversion_rate"] == 0.0

    def _run(self, user, ch):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from app.db.postgres import get_db

        db = _db_returning_user(user)
        app.dependency_overrides[get_clickhouse] = lambda: ch
        app.dependency_overrides[get_db] = lambda: db

        async def _go():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get(
                    f"/v1/analytics/funnel?campaign_id={self.CAMPAIGN_ID}"
                    f"&date_from={DATE_FROM}&date_to={DATE_TO}",
                    headers=_auth_headers(user.id),
                )

        resp = asyncio.get_event_loop().run_until_complete(_go())
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        return resp.json()


# ── /analytics/geo ────────────────────────────────────────────────────────────

class TestGeo:
    CAMPAIGN_ID = str(uuid.uuid4())

    def test_returns_list(self, user):
        ch = _make_ch_mock([
            ("Москва", 200, 15, 45000.0),
            ("Санкт-Петербург", 80, 5, 12000.0),
        ])
        body = self._run(user, ch)
        assert len(body) == 2
        assert body[0]["region"] == "Москва"

    def test_conversion_rate_computed(self, user):
        ch = _make_ch_mock([("Казань", 100, 10, 5000.0)])
        body = self._run(user, ch)
        assert body[0]["conversion_rate"] == pytest.approx(0.1)

    def test_empty_returns_empty_list(self, user):
        ch = _make_ch_mock([])
        body = self._run(user, ch)
        assert body == []

    def _run(self, user, ch):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from app.db.postgres import get_db

        db = _db_returning_user(user)
        app.dependency_overrides[get_clickhouse] = lambda: ch
        app.dependency_overrides[get_db] = lambda: db

        async def _go():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get(
                    f"/v1/analytics/geo?campaign_id={self.CAMPAIGN_ID}"
                    f"&date_from={DATE_FROM}&date_to={DATE_TO}",
                    headers=_auth_headers(user.id),
                )

        resp = asyncio.get_event_loop().run_until_complete(_go())
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        return resp.json()


# ── /attribution/log ──────────────────────────────────────────────────────────

class TestAttributionLog:
    def test_returns_list_of_entries(self, user):
        ch = _make_ch_mock([self._sample_row()])
        body = self._run(user, ch)
        assert len(body) == 1
        assert "order_id" in body[0]
        assert "confidence" in body[0]
        assert "attribution_method" in body[0]

    def test_empty_returns_empty_list(self, user):
        ch = _make_ch_mock([])
        body = self._run(user, ch)
        assert body == []

    def test_campaign_filter_passed(self, user):
        campaign_id = str(uuid.uuid4())
        ch = _make_ch_mock([])
        self._run(user, ch, extra=f"&campaign_id={campaign_id}")
        call_args = ch.query.call_args
        assert "campaign_id" in call_args[1]["parameters"]

    def test_min_confidence_filter_passed(self, user):
        ch = _make_ch_mock([])
        self._run(user, ch, extra="&min_confidence=0.8")
        call_args = ch.query.call_args
        assert call_args[1]["parameters"]["min_confidence"] == 0.8

    def _sample_row(self):
        return (
            str(uuid.uuid4()),  # order_id
            str(uuid.uuid4()),  # campaign_id
            "ABCDE12",          # trax_id
            "ozon",             # marketplace
            "vk_ads",           # ad_platform
            "SKU-001",          # product_id
            2990.0,             # order_amount
            NOW,                # click_at
            NOW,                # order_at
            2.5,                # time_to_order_hours
            0.92,               # confidence
            "probabilistic",    # attribution_method
        )

    def _run(self, user, ch, extra=""):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from app.db.postgres import get_db

        db = _db_returning_user(user)
        app.dependency_overrides[get_clickhouse] = lambda: ch
        app.dependency_overrides[get_db] = lambda: db

        async def _go():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get(
                    f"/v1/attribution/log?date_from={DATE_FROM}&date_to={DATE_TO}{extra}",
                    headers=_auth_headers(user.id),
                )

        resp = asyncio.get_event_loop().run_until_complete(_go())
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        return resp.json()


# ── fixture shim ─────────────────────────────────────────────────────────────

@pytest.fixture
def client_factory():
    """Placeholder so TestOverview can take it as a param without error."""
    return None
