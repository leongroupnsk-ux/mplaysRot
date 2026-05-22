"""
Integration tests for the auth flow:
  POST /auth/register  → 201 + tokens
  POST /auth/login     → 200 + tokens
  GET  /auth/me        → 200 + user data
  POST /auth/refresh   → 200 + new tokens  (rotation)
  Error cases: duplicate email, wrong password, bad token
"""
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
import uuid

import pytest

from app.utils.jwt import (
    hash_password, create_refresh_token,
    decode_token, hash_refresh_token,
)
from app.models.user import User, RefreshToken
from tests.conftest import make_user


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_result(obj):
    """Wraps obj so result.scalar_one_or_none() returns it."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = obj
    return r


def _set_execute_sequence(mock_db, *results):
    """Configure mock_db.execute to return results in sequence."""
    mock_db.execute = AsyncMock(side_effect=[_mock_result(r) for r in results])


# ── register ──────────────────────────────────────────────────────────────────

async def test_register_returns_201_with_tokens(client):
    http, db = client
    # execute(select user by email) → None (not registered yet)
    # execute(insert refresh token) → doesn't matter
    _set_execute_sequence(db, None, None)

    resp = await http.post("/v1/auth/register", json={
        "email": "new@example.com",
        "password": "strongpass123",
        "full_name": "Новый Юзер",
    })

    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_register_access_token_is_valid_jwt(client):
    http, db = client
    _set_execute_sequence(db, None, None)

    resp = await http.post("/v1/auth/register", json={
        "email": "jwt@example.com",
        "password": "pass123456",
        "full_name": "JWT Тест",
    })
    token = resp.json()["access_token"]
    payload = decode_token(token)
    assert payload["type"] == "access"
    assert "sub" in payload


async def test_register_duplicate_email_returns_409(client):
    http, db = client
    existing_user = make_user(email="dup@example.com")
    # First execute → finds existing user
    _set_execute_sequence(db, existing_user)

    resp = await http.post("/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "pass123456",
        "full_name": "Дубликат",
    })

    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


async def test_register_missing_fields_returns_422(client):
    http, db = client
    resp = await http.post("/v1/auth/register", json={"email": "only@email.com"})
    assert resp.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────

async def test_login_correct_credentials_returns_200(client):
    http, db = client
    user = make_user(
        email="login@example.com",
        password_hash=hash_password("correctpass"),
    )
    _set_execute_sequence(db, user, None)

    resp = await http.post("/v1/auth/login", json={
        "email": "login@example.com",
        "password": "correctpass",
    })

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_returns_401(client):
    http, db = client
    user = make_user(
        email="user@example.com",
        password_hash=hash_password("realpassword"),
    )
    _set_execute_sequence(db, user)

    resp = await http.post("/v1/auth/login", json={
        "email": "user@example.com",
        "password": "wrongpassword",
    })

    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


async def test_login_nonexistent_user_returns_401(client):
    http, db = client
    _set_execute_sequence(db, None)

    resp = await http.post("/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "anypassword",
    })

    assert resp.status_code == 401


async def test_login_inactive_user_returns_403(client):
    http, db = client
    user = make_user(
        email="disabled@example.com",
        password_hash=hash_password("pass123"),
    )
    user.is_active = False
    _set_execute_sequence(db, user)

    resp = await http.post("/v1/auth/login", json={
        "email": "disabled@example.com",
        "password": "pass123",
    })

    assert resp.status_code == 403
    assert "disabled" in resp.json()["detail"]


# ── /me ───────────────────────────────────────────────────────────────────────

async def test_me_with_valid_access_token_returns_user(client):
    http, db = client
    user = make_user(email="me@example.com")
    access_token = create_refresh_token.__module__  # just for import check

    from app.utils.jwt import create_access_token
    token = create_access_token(str(user.id))

    # get_current_user does: execute(select User by id)
    _set_execute_sequence(db, user)

    resp = await http.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert body["role"] == "owner"
    assert "password_hash" not in body


async def test_me_without_token_returns_403(client):
    # FastAPI HTTPBearer returns 403 when no Authorization header is present
    http, db = client
    resp = await http.get("/v1/auth/me")
    assert resp.status_code == 403


async def test_me_with_refresh_token_returns_401(client):
    http, db = client
    refresh = create_refresh_token(str(uuid.uuid4()))
    resp = await http.get("/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"})
    assert resp.status_code == 401


async def test_me_with_garbage_token_returns_401(client):
    http, db = client
    resp = await http.get("/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────

async def test_refresh_with_valid_token_returns_new_pair(client):
    http, db = client
    user_id = uuid.uuid4()
    refresh_tok = create_refresh_token(str(user_id))

    stored = MagicMock(spec=RefreshToken)
    stored.id = uuid.uuid4()
    stored.user_id = user_id
    stored.token_hash = hash_refresh_token(refresh_tok)
    stored.expires_at = datetime.now(timezone.utc) + timedelta(days=29)

    _set_execute_sequence(db, stored, None)

    resp = await http.post("/v1/auth/refresh", json={"refresh_token": refresh_tok})

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    # Verify the new refresh token is a valid JWT (rotation happened)
    new_payload = decode_token(body["refresh_token"])
    assert new_payload["type"] == "refresh"
    assert new_payload["sub"] == str(user_id)


async def test_refresh_with_access_token_returns_401(client):
    http, db = client
    from app.utils.jwt import create_access_token
    access = create_access_token(str(uuid.uuid4()))

    resp = await http.post("/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


async def test_refresh_with_unknown_token_returns_401(client):
    http, db = client
    valid_refresh = create_refresh_token(str(uuid.uuid4()))
    # DB returns None — token not stored
    _set_execute_sequence(db, None)

    resp = await http.post("/v1/auth/refresh", json={"refresh_token": valid_refresh})
    assert resp.status_code == 401


async def test_refresh_with_garbage_returns_401(client):
    http, db = client
    resp = await http.post("/v1/auth/refresh", json={"refresh_token": "garbage.token"})
    assert resp.status_code == 401


async def test_refresh_missing_body_field_returns_401(client):
    http, db = client
    resp = await http.post("/v1/auth/refresh", json={})
    assert resp.status_code == 401
