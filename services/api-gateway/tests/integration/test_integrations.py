"""
Integration tests for /integrations router.

  GET    /integrations                    → list all connections
  POST   /integrations/marketplace        → connect marketplace
  POST   /integrations/ad                 → connect ad platform
  DELETE /integrations/{id}              → remove integration
  POST   /integrations/{id}/validate     → re-validate connection

FastAPI HTTPBearer returns 403 (not 401) when no credentials are provided.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.jwt import create_access_token
from tests.conftest import make_user

NOW = datetime.now(timezone.utc)


# ── helpers ───────────────────────────────────────────────────────────────────

def _auth_headers(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _make_mp_connection(user_id: uuid.UUID) -> MagicMock:
    c = MagicMock()
    c.id = str(uuid.uuid4())       # IntegrationResponse.id is str
    c.user_id = user_id
    c.marketplace = "ozon"
    c.marketplace_name = "Мой магазин Ozon"
    c.api_key_enc = b"encrypted_key"
    c.client_id = "12345"
    c.seller_id = "67890"
    c.status = "active"
    c.last_synced_at = NOW
    c.created_at = NOW
    return c


def _make_ad_connection(user_id: uuid.UUID) -> MagicMock:
    c = MagicMock()
    c.id = str(uuid.uuid4())       # IntegrationResponse.id is str
    c.user_id = user_id
    c.platform = "vk_ads"
    c.account_name = "VK Ads Account"
    c.account_id = "vk_acc_001"
    c.access_token_enc = b"encrypted_token"
    c.refresh_token_enc = None
    c.status = "active"
    c.last_synced_at = NOW
    c.created_at = NOW
    return c


def _mock_result_obj(obj):
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    r.scalars.return_value.all.return_value = [obj] if obj is not None else []
    return r


def _mock_result_list(items: list):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    r.scalar_one_or_none.return_value = items[0] if items else None
    return r


# ── GET /integrations ─────────────────────────────────────────────────────────

async def test_list_integrations_returns_combined_list(client):
    http, db = client
    user = make_user()
    mp = _make_mp_connection(user.id)
    ad = _make_ad_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_list([mp]),
        _mock_result_list([ad]),
    ])

    resp = await http.get("/v1/integrations/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    types = {item["type"] for item in body}
    assert types == {"marketplace", "ad_platform"}


async def test_list_integrations_empty_returns_empty_list(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_list([]),
        _mock_result_list([]),
    ])

    resp = await http.get("/v1/integrations/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_integrations_without_auth_returns_403(client):
    http, db = client
    resp = await http.get("/v1/integrations/")
    assert resp.status_code == 403


# ── POST /integrations/marketplace ───────────────────────────────────────────

async def test_connect_marketplace_returns_201(client):
    http, db = client
    user = make_user()
    mock_conn = _make_mp_connection(user.id)

    db.execute = AsyncMock(return_value=_mock_result_obj(user))
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.routers.integrations._validate_marketplace", return_value=(True, "ok")), \
         patch("app.routers.integrations._ensure_store", return_value=None), \
         patch("app.routers.integrations.MarketplaceConnection", return_value=mock_conn):

        resp = await http.post(
            "/v1/integrations/marketplace",
            json={
                "provider": "ozon",
                "api_key": "test-api-key",
                "client_id": "12345",
                "seller_id": "67890",
            },
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "marketplace"
    assert body["provider"] == "ozon"


async def test_connect_marketplace_validation_fail_sets_error_status(client):
    http, db = client
    user = make_user()
    mock_conn = _make_mp_connection(user.id)
    mock_conn.status = "error"

    db.execute = AsyncMock(return_value=_mock_result_obj(user))
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.routers.integrations._validate_marketplace", return_value=(False, "bad key")), \
         patch("app.routers.integrations._ensure_store", return_value=None), \
         patch("app.routers.integrations.MarketplaceConnection", return_value=mock_conn):

        resp = await http.post(
            "/v1/integrations/marketplace",
            json={"provider": "ozon", "api_key": "bad-key"},
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 201
    assert resp.json()["status"] == "error"


async def test_connect_marketplace_invalid_provider_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.post(
        "/v1/integrations/marketplace",
        json={"provider": "aliexpress", "api_key": "key"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 422


async def test_connect_marketplace_missing_api_key_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.post(
        "/v1/integrations/marketplace",
        json={"provider": "ozon"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 422


# ── POST /integrations/ad ─────────────────────────────────────────────────────

async def test_connect_ad_platform_returns_201(client):
    http, db = client
    user = make_user()
    mock_conn = _make_ad_connection(user.id)

    db.execute = AsyncMock(return_value=_mock_result_obj(user))
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.routers.integrations._validate_ad", return_value=(True, "ok")), \
         patch("app.routers.integrations.AdPlatformConnection", return_value=mock_conn):

        resp = await http.post(
            "/v1/integrations/ad",
            json={
                "provider": "vk_ads",
                "access_token": "test-token",
                "account_id": "vk_acc_001",
                "account_name": "VK Ads Account",
            },
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "ad_platform"
    assert body["provider"] == "vk_ads"
    assert body["status"] == "active"


async def test_connect_ad_platform_validation_fail_sets_error_status(client):
    http, db = client
    user = make_user()
    mock_conn = _make_ad_connection(user.id)
    mock_conn.status = "error"

    db.execute = AsyncMock(return_value=_mock_result_obj(user))
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    with patch("app.routers.integrations._validate_ad", return_value=(False, "invalid token")), \
         patch("app.routers.integrations.AdPlatformConnection", return_value=mock_conn):

        resp = await http.post(
            "/v1/integrations/ad",
            json={"provider": "yandex_direct", "access_token": "bad-token"},
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 201
    assert resp.json()["status"] == "error"


async def test_connect_ad_invalid_provider_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.post(
        "/v1/integrations/ad",
        json={"provider": "facebook_ads", "access_token": "tok"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 422


# ── DELETE /integrations/{id} ─────────────────────────────────────────────────

async def test_delete_marketplace_integration_returns_204(client):
    http, db = client
    user = make_user()
    mp = _make_mp_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(mp),
    ])
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    resp = await http.delete(f"/v1/integrations/{mp.id}", headers=_auth_headers(user.id))
    assert resp.status_code == 204


async def test_delete_ad_integration_returns_204(client):
    http, db = client
    user = make_user()
    ad = _make_ad_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),   # not found in marketplace
        _mock_result_obj(ad),     # found in ad platform
    ])
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    resp = await http.delete(f"/v1/integrations/{ad.id}", headers=_auth_headers(user.id))
    assert resp.status_code == 204


async def test_delete_nonexistent_integration_returns_404(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
        _mock_result_obj(None),
    ])

    resp = await http.delete(f"/v1/integrations/{uuid.uuid4()}", headers=_auth_headers(user.id))
    assert resp.status_code == 404


async def test_delete_integration_without_auth_returns_403(client):
    http, db = client
    resp = await http.delete(f"/v1/integrations/{uuid.uuid4()}")
    assert resp.status_code == 403


# ── POST /integrations/{id}/validate ─────────────────────────────────────────

async def test_validate_marketplace_returns_ok(client):
    http, db = client
    user = make_user()
    mp = _make_mp_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(mp),
    ])
    db.commit = AsyncMock()

    with patch("app.routers.integrations._validate_marketplace", return_value=(True, "Connection OK")), \
         patch("app.routers.integrations._ensure_store", return_value=None):

        resp = await http.post(
            f"/v1/integrations/{mp.id}/validate",
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "message" in body


async def test_validate_ad_returns_ok(client):
    http, db = client
    user = make_user()
    ad = _make_ad_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),  # not marketplace
        _mock_result_obj(ad),    # ad platform found
    ])
    db.commit = AsyncMock()

    with patch("app.routers.integrations._validate_ad", return_value=(True, "ok")):
        resp = await http.post(
            f"/v1/integrations/{ad.id}/validate",
            headers=_auth_headers(user.id),
        )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True


async def test_validate_nonexistent_integration_returns_404(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
        _mock_result_obj(None),
    ])

    resp = await http.post(
        f"/v1/integrations/{uuid.uuid4()}/validate",
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 404


# ── response shape ────────────────────────────────────────────────────────────

async def test_integration_response_has_required_fields(client):
    http, db = client
    user = make_user()
    mp = _make_mp_connection(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_list([mp]),
        _mock_result_list([]),
    ])

    resp = await http.get("/v1/integrations/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    item = resp.json()[0]
    for field in ("id", "type", "provider", "status", "created_at"):
        assert field in item, f"Missing field: {field}"
