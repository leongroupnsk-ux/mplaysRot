"""Unit tests for JWT and password utilities (app/utils/jwt.py)."""
import time
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from jose import jwt as jose_jwt

from app.utils.jwt import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)
from app.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_produces_bcrypt_hash():
    h = hash_password("secret123")
    assert h.startswith("$2b$") or h.startswith("$2a$")


def test_verify_password_correct():
    plain = "my-secure-password"
    assert verify_password(plain, hash_password(plain))


def test_verify_password_wrong():
    assert not verify_password("wrong", hash_password("correct"))


def test_hash_password_different_salts():
    plain = "same-password"
    assert hash_password(plain) != hash_password(plain)


# ── Access token ──────────────────────────────────────────────────────────────

def test_create_access_token_structure():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload


def test_access_token_expires_in_future():
    token = create_access_token(str(uuid.uuid4()))
    payload = decode_token(token)
    assert payload["exp"] > time.time()


def test_access_token_expiry_matches_settings():
    before = datetime.now(timezone.utc)
    token = create_access_token(str(uuid.uuid4()))
    payload = decode_token(token)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected = before + timedelta(minutes=settings.jwt_expire_minutes)
    # Allow 5-second tolerance for test execution time
    assert abs((exp - expected).total_seconds()) < 5


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_create_refresh_token_type():
    token = create_refresh_token(str(uuid.uuid4()))
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_refresh_token_expires_in_30_days():
    token = create_refresh_token(str(uuid.uuid4()))
    payload = decode_token(token)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    assert 29 <= delta.days <= 30


def test_access_and_refresh_tokens_are_different():
    uid = str(uuid.uuid4())
    assert create_access_token(uid) != create_refresh_token(uid)


# ── decode_token ──────────────────────────────────────────────────────────────

def test_decode_token_tampered_signature_raises():
    from jose import JWTError
    token = create_access_token(str(uuid.uuid4()))
    tampered = token[:-4] + "XXXX"
    with pytest.raises(JWTError):
        decode_token(tampered)


def test_decode_token_wrong_key_raises():
    from jose import JWTError
    token = jose_jwt.encode(
        {"sub": "user", "exp": time.time() + 3600, "type": "access"},
        "wrong-key",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(JWTError):
        decode_token(token)


# ── hash_refresh_token ────────────────────────────────────────────────────────

def test_hash_refresh_token_is_deterministic():
    token = "some.jwt.token"
    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_hash_refresh_token_is_sha256():
    import hashlib
    token = "test-token"
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert hash_refresh_token(token) == expected


def test_hash_refresh_token_different_inputs_differ():
    assert hash_refresh_token("token-a") != hash_refresh_token("token-b")
