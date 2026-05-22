"""
Integration tests for /campaigns router.

All DB and Redis calls are mocked — no live infrastructure needed.
FastAPI HTTPBearer returns 403 (not 401) when no credentials are provided.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.jwt import create_access_token
from tests.conftest import make_user

NOW = datetime.now(timezone.utc)

CAMPAIGN_PAYLOAD = {
    "name": "Test Campaign",
    "marketplace": "ozon",
    "ad_platform": "vk_ads",
    "destination_url": "https://ozon.ru/product/123",
    "budget": 50000,
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _auth_headers(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _make_campaign(user_id: uuid.UUID, name: str = "Test Campaign") -> MagicMock:
    c = MagicMock()
    c.id = str(uuid.uuid4())
    c.user_id = user_id
    c.name = name
    c.marketplace = "ozon"
    c.ad_platform = "vk_ads"
    c.destination_url = "https://ozon.ru/product/123"
    c.budget = 50000.0
    c.is_active = True
    c.utm_source = None
    c.utm_medium = None
    c.utm_campaign = None
    c.created_at = NOW
    c.updated_at = NOW
    return c


def _make_tracking_link(campaign_id: str) -> MagicMock:
    link = MagicMock()
    link.trax_id = "ABCDE12"
    link.campaign_id = campaign_id
    link.destination_url = "https://ozon.ru/product/123?trax_id=ABCDE12"
    link.label = "default"
    link.utm_source = None
    link.is_active = True
    link.created_at = NOW
    return link


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


def _mock_result_scalar(value):
    """Mock for scalar_one() — used for COUNT(*) results."""
    r = MagicMock()
    r.scalar_one.return_value = value
    return r


# ── POST /campaigns ───────────────────────────────────────────────────────────

async def test_create_campaign_returns_201(client):
    http, db = client
    user = make_user()
    headers = _auth_headers(user.id)
    campaign = _make_campaign(user.id)

    # get_current_user query
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    # Patch the service so no real ORM object or Redis call is made
    with patch("app.routers.campaigns.svc.create_campaign", new=AsyncMock(return_value=campaign)):
        resp = await http.post("/v1/campaigns/", json=CAMPAIGN_PAYLOAD, headers=headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Campaign"
    assert body["marketplace"] == "ozon"
    assert body["ad_platform"] == "vk_ads"
    assert body["is_active"] is True


async def test_create_campaign_without_auth_returns_403(client):
    http, db = client
    resp = await http.post("/v1/campaigns/", json=CAMPAIGN_PAYLOAD)
    assert resp.status_code == 403


async def test_create_campaign_invalid_marketplace_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    payload = {**CAMPAIGN_PAYLOAD, "marketplace": "invalid_marketplace"}
    resp = await http.post("/v1/campaigns/", json=payload, headers=_auth_headers(user.id))
    assert resp.status_code == 422


async def test_create_campaign_invalid_url_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    payload = {**CAMPAIGN_PAYLOAD, "destination_url": "not-a-url"}
    resp = await http.post("/v1/campaigns/", json=payload, headers=_auth_headers(user.id))
    assert resp.status_code == 422


async def test_create_campaign_missing_required_fields_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.post("/v1/campaigns/", json={"name": "Only name"}, headers=_auth_headers(user.id))
    assert resp.status_code == 422


# ── GET /campaigns ────────────────────────────────────────────────────────────

async def test_list_campaigns_returns_200_with_items(client):
    http, db = client
    user = make_user()
    c1 = _make_campaign(user.id, "Campaign A")
    c2 = _make_campaign(user.id, "Campaign B")

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),       # get_current_user
        _mock_result_scalar(2),       # COUNT(*)
        _mock_result_list([c1, c2]),  # paginated items
    ])

    resp = await http.get("/v1/campaigns/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["items"]) == 2
    assert body["items"][0]["name"] == "Campaign A"


async def test_list_campaigns_empty_returns_empty_list(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(0),
        _mock_result_list([]),
    ])

    resp = await http.get("/v1/campaigns/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


async def test_list_campaigns_pagination_params(client):
    http, db = client
    user = make_user()
    campaigns = [_make_campaign(user.id, f"C{i}") for i in range(3)]

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(10),
        _mock_result_list(campaigns),
    ])

    resp = await http.get("/v1/campaigns/?page=2&page_size=3", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["page_size"] == 3
    assert body["total"] == 10
    assert body["pages"] == 4  # ceil(10/3)


async def test_list_campaigns_page_size_over_max_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.get("/v1/campaigns/?page_size=200", headers=_auth_headers(user.id))
    assert resp.status_code == 422


async def test_list_campaigns_without_auth_returns_403(client):
    http, db = client
    resp = await http.get("/v1/campaigns/")
    assert resp.status_code == 403


# ── GET /campaigns/{id} ───────────────────────────────────────────────────────

async def test_get_campaign_returns_200(client):
    http, db = client
    user = make_user()
    campaign = _make_campaign(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(campaign),
    ])

    resp = await http.get(f"/v1/campaigns/{campaign.id}", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Campaign"


async def test_get_campaign_not_found_returns_404(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
    ])

    resp = await http.get(f"/v1/campaigns/{uuid.uuid4()}", headers=_auth_headers(user.id))
    assert resp.status_code == 404


# ── PATCH /campaigns/{id} ─────────────────────────────────────────────────────

async def test_patch_campaign_name_returns_200(client):
    http, db = client
    user = make_user()
    campaign = _make_campaign(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(campaign),  # get_campaign inside update_campaign
        MagicMock(),                 # execute(update(...))
    ])
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    resp = await http.patch(
        f"/v1/campaigns/{campaign.id}",
        json={"name": "Renamed"},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 200


async def test_patch_campaign_not_found_returns_404(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
    ])

    resp = await http.patch(
        f"/v1/campaigns/{uuid.uuid4()}",
        json={"is_active": False},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 404


# ── DELETE /campaigns/{id} ────────────────────────────────────────────────────

async def test_delete_campaign_returns_204(client):
    http, db = client
    user = make_user()
    campaign = _make_campaign(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(campaign),  # get_campaign
        _mock_result_list([]),       # select tracking links
        MagicMock(),                 # delete execute
    ])
    db.commit = AsyncMock()

    with patch("app.services.campaigns.get_redis") as mock_redis:
        mock_redis.return_value = AsyncMock()
        resp = await http.delete(f"/v1/campaigns/{campaign.id}", headers=_auth_headers(user.id))

    assert resp.status_code == 204


async def test_delete_campaign_not_found_returns_404(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
    ])

    resp = await http.delete(f"/v1/campaigns/{uuid.uuid4()}", headers=_auth_headers(user.id))
    assert resp.status_code == 404


# ── GET /campaigns/{id}/links ─────────────────────────────────────────────────

async def test_get_tracking_links_returns_list(client):
    http, db = client
    user = make_user()
    campaign = _make_campaign(user.id)
    link = _make_tracking_link(str(campaign.id))

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(campaign),  # get_campaign
        _mock_result_list([link]),   # select tracking links
    ])

    resp = await http.get(f"/v1/campaigns/{campaign.id}/links", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["trax_id"] == "ABCDE12"
    assert "tracking_url" in body[0]
