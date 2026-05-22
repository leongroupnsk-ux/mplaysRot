"""
Integration tests for /connections router.

All DB calls are mocked — no live infrastructure needed.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.db.postgres import get_db
from app.main import app
from app.utils.jwt import create_access_token
from tests.conftest import make_user, make_mock_db

NOW = datetime.now(timezone.utc)


def _auth(user_id) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _mock_conn(cls, user_id, platform_key="platform", platform_val="vk_ads"):
    c = MagicMock(spec=cls)
    c.id = uuid.uuid4()
    c.user_id = user_id
    setattr(c, platform_key, platform_val)
    c.account_id = "acc-123"
    c.account_name = "Test Account"
    c.client_id = "cli-456"
    c.marketplace_name = "Ozon"
    c.is_active = True
    c.last_synced_at = None
    c.created_at = NOW
    return c


def _db_with_user_and_result(user, result_rows):
    """DB mock: first execute returns user, second returns the query result."""
    db = make_mock_db()
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user

    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = result_rows

    db.execute = AsyncMock(side_effect=[user_result, list_result])
    return db


def _db_user_only(user):
    db = make_mock_db()
    r = MagicMock()
    r.scalar_one_or_none.return_value = user
    db.execute = AsyncMock(return_value=r)
    return db


# ── Ad platform list ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_ad_connections_returns_200():
    from app.models.connections import AdPlatformConnection
    user = make_user()
    conn = _mock_conn(AdPlatformConnection, user.id, "platform", "vk_ads")
    db = _db_with_user_and_result(user, [conn])
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/v1/connections/ad-platforms", headers=_auth(user.id))

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["platform"] == "vk_ads"


@pytest.mark.asyncio
async def test_list_ad_connections_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/v1/connections/ad-platforms")
    assert resp.status_code == 403


# ── Ad platform create ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_ad_connection_returns_201():
    from app.models.connections import AdPlatformConnection
    user = make_user()
    conn = _mock_conn(AdPlatformConnection, user.id, "platform", "telegram_ads")
    conn.id = uuid.uuid4()
    conn.account_id = None
    conn.account_name = None

    db = _db_user_only(user)
    db.refresh = AsyncMock(side_effect=lambda obj: None)

    with patch("app.routers.connections.encrypt_token", return_value="enc-token"):
        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/v1/connections/ad-platforms",
                json={"platform": "telegram_ads", "access_token": "tok-abc"},
                headers=_auth(user.id),
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_ad_connection_unknown_platform_returns_422():
    user = make_user()
    db = _db_user_only(user)
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/v1/connections/ad-platforms",
            json={"platform": "tiktok_ads", "access_token": "tok"},
            headers=_auth(user.id),
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


# ── Ad platform delete ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_ad_connection_returns_204():
    from app.models.connections import AdPlatformConnection
    user = make_user()
    conn_id = uuid.uuid4()
    conn = _mock_conn(AdPlatformConnection, user.id, "platform", "vk_ads")
    conn.id = conn_id

    db = _db_user_only(user)
    # First call: get_current_user; second call: find connection
    conn_result = MagicMock()
    conn_result.scalar_one_or_none.return_value = conn
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    db.execute = AsyncMock(side_effect=[user_result, conn_result])

    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.delete(
            f"/v1/connections/ad-platforms/{conn_id}",
            headers=_auth(user.id),
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_ad_connection_not_found_returns_404():
    user = make_user()
    conn_id = uuid.uuid4()

    db = make_mock_db()
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(side_effect=[user_result, not_found])

    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.delete(
            f"/v1/connections/ad-platforms/{conn_id}",
            headers=_auth(user.id),
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 404


# ── Marketplace list ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_marketplace_connections_returns_200():
    from app.models.connections import MarketplaceConnection
    user = make_user()
    conn = _mock_conn(MarketplaceConnection, user.id, "marketplace", "ozon")
    db = _db_with_user_and_result(user, [conn])
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/v1/connections/marketplaces", headers=_auth(user.id))

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["marketplace"] == "ozon"


# ── Marketplace create ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_marketplace_connection_returns_201():
    from app.models.connections import MarketplaceConnection
    user = make_user()
    conn = _mock_conn(MarketplaceConnection, user.id, "marketplace", "wildberries")
    conn.id = uuid.uuid4()
    conn.client_id = None
    conn.marketplace_name = None

    db = _db_user_only(user)
    db.refresh = AsyncMock(side_effect=lambda obj: None)

    with patch("app.routers.connections.encrypt_token", return_value="enc-key"):
        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/v1/connections/marketplaces",
                json={"marketplace": "wildberries", "api_key": "key-123"},
                headers=_auth(user.id),
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_marketplace_unknown_returns_422():
    user = make_user()
    db = _db_user_only(user)
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/v1/connections/marketplaces",
            json={"marketplace": "amazon", "api_key": "key"},
            headers=_auth(user.id),
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422
