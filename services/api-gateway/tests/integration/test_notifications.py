"""
Integration tests for /notifications router.

  GET  /notifications              → list (all / unread_only)
  POST /notifications/read-all     → mark all read
  POST /notifications/{id}/read    → mark single read

FastAPI HTTPBearer returns 403 (not 401) when no credentials are provided.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.utils.jwt import create_access_token
from tests.conftest import make_user

NOW = datetime.now(timezone.utc)


# ── helpers ───────────────────────────────────────────────────────────────────

def _auth_headers(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _make_notification(user_id: uuid.UUID, is_read: bool = False) -> MagicMock:
    n = MagicMock()
    n.id = str(uuid.uuid4())      # NotificationResponse.id is str
    n.user_id = str(user_id)
    n.campaign_id = None
    n.type = "low_roas"
    n.title = "Низкий ROAS"
    n.body = "ROAS кампании упал ниже порога"
    n.is_read = is_read
    n.payload = None
    n.created_at = NOW
    return n


def _mock_result_list(items: list):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    r.scalar_one_or_none.return_value = items[0] if items else None
    return r


def _mock_result_obj(obj):
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    r.scalars.return_value.all.return_value = [obj] if obj is not None else []
    return r


def _mock_result_scalar(value):
    r = MagicMock()
    r.scalar_one.return_value = value
    return r


# ── GET /notifications ────────────────────────────────────────────────────────

async def test_list_notifications_returns_200_with_items(client):
    http, db = client
    user = make_user()
    n1 = _make_notification(user.id)
    n2 = _make_notification(user.id, is_read=True)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),        # get_current_user
        _mock_result_scalar(2),        # COUNT(*)
        _mock_result_list([n1, n2]),   # paginated items
    ])

    resp = await http.get("/v1/notifications/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 50
    assert len(body["items"]) == 2
    assert body["items"][0]["type"] == "low_roas"
    assert body["items"][0]["title"] == "Низкий ROAS"


async def test_list_notifications_empty_returns_empty_list(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(0),
        _mock_result_list([]),
    ])

    resp = await http.get("/v1/notifications/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


async def test_list_notifications_unread_only(client):
    http, db = client
    user = make_user()
    unread = _make_notification(user.id, is_read=False)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(1),
        _mock_result_list([unread]),
    ])

    resp = await http.get("/v1/notifications/?unread_only=true", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert all(not n["is_read"] for n in body["items"])


async def test_list_notifications_respects_page_size(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(0),
        _mock_result_list([]),
    ])

    resp = await http.get("/v1/notifications/?page_size=5", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    assert resp.json()["page_size"] == 5


async def test_list_notifications_page_size_over_max_returns_422(client):
    http, db = client
    user = make_user()
    db.execute = AsyncMock(return_value=_mock_result_obj(user))

    resp = await http.get("/v1/notifications/?page_size=300", headers=_auth_headers(user.id))
    assert resp.status_code == 422


async def test_list_notifications_pagination_envelope(client):
    http, db = client
    user = make_user()
    items = [_make_notification(user.id) for _ in range(3)]

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(53),
        _mock_result_list(items),
    ])

    resp = await http.get("/v1/notifications/?page=2&page_size=50", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["total"] == 53
    assert body["pages"] == 2  # ceil(53/50)


async def test_list_notifications_without_auth_returns_403(client):
    http, db = client
    resp = await http.get("/v1/notifications/")
    assert resp.status_code == 403


# ── POST /notifications/read-all ──────────────────────────────────────────────

async def test_mark_all_read_returns_ok(client):
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        MagicMock(),  # update execute
    ])
    db.commit = AsyncMock()

    resp = await http.post("/v1/notifications/read-all", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


async def test_mark_all_read_without_auth_returns_403(client):
    http, db = client
    resp = await http.post("/v1/notifications/read-all")
    assert resp.status_code == 403


# ── POST /notifications/{id}/read ─────────────────────────────────────────────

async def test_mark_single_read_returns_ok(client):
    http, db = client
    user = make_user()
    notif = _make_notification(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(notif),
    ])
    db.commit = AsyncMock()

    resp = await http.post(
        f"/v1/notifications/{notif.id}/read",
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert notif.is_read is True


async def test_mark_single_read_not_found_still_returns_ok(client):
    """Marking a non-existent notification is a no-op — returns ok to avoid info leakage."""
    http, db = client
    user = make_user()

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_obj(None),
    ])
    db.commit = AsyncMock()

    resp = await http.post(
        f"/v1/notifications/{uuid.uuid4()}/read",
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


async def test_mark_single_read_without_auth_returns_403(client):
    http, db = client
    resp = await http.post(f"/v1/notifications/{uuid.uuid4()}/read")
    assert resp.status_code == 403


# ── response shape ────────────────────────────────────────────────────────────

async def test_notification_response_has_required_fields(client):
    http, db = client
    user = make_user()
    notif = _make_notification(user.id)

    db.execute = AsyncMock(side_effect=[
        _mock_result_obj(user),
        _mock_result_scalar(1),
        _mock_result_list([notif]),
    ])

    resp = await http.get("/v1/notifications/", headers=_auth_headers(user.id))
    assert resp.status_code == 200
    body = resp.json()
    n = body["items"][0]
    for field in ("id", "type", "title", "body", "is_read", "created_at"):
        assert field in n, f"Missing field: {field}"
