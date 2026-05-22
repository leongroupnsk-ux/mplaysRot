"""
Unit tests for the rate-limiting helper in app.utils.limiter.

We test _real_ip() in isolation — no Redis, no HTTP server needed.
The 429 path is tested via the test client with the in-memory limiter
(overridden storage_uri so tests don't need a real Redis instance).
"""
import pytest
from unittest.mock import MagicMock
from app.utils.limiter import _real_ip


def _make_request(connecting_ip: str, forwarded_for: str | None = None) -> MagicMock:
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = connecting_ip
    headers: dict[str, str] = {}
    if forwarded_for is not None:
        headers["X-Forwarded-For"] = forwarded_for
    req.headers = headers
    return req


# ── _real_ip ──────────────────────────────────────────────────────────────────

class TestRealIp:
    def test_public_ip_no_forwarded_for(self):
        req = _make_request("8.8.8.8")
        assert _real_ip(req) == "8.8.8.8"

    def test_public_ip_ignores_forwarded_for(self):
        # Connecting IP is public → don't trust XFF (could be spoofed)
        req = _make_request("8.8.8.8", forwarded_for="1.2.3.4")
        assert _real_ip(req) == "8.8.8.8"

    def test_private_proxy_uses_xff(self):
        req = _make_request("10.0.0.1", forwarded_for="203.0.113.5")
        assert _real_ip(req) == "203.0.113.5"

    def test_localhost_proxy_uses_xff(self):
        req = _make_request("127.0.0.1", forwarded_for="203.0.113.42")
        assert _real_ip(req) == "203.0.113.42"

    def test_xff_chain_uses_first_entry(self):
        req = _make_request("172.20.0.1", forwarded_for="203.0.113.5, 10.0.0.2")
        assert _real_ip(req) == "203.0.113.5"

    def test_xff_invalid_ip_falls_back_to_connecting(self):
        req = _make_request("10.0.0.1", forwarded_for="not-an-ip")
        assert _real_ip(req) == "10.0.0.1"

    def test_no_client(self):
        req = _make_request("127.0.0.1", forwarded_for="203.0.113.9")
        req.client = None
        # When client is None we fall back to "127.0.0.1" → trusted → use XFF
        assert _real_ip(req) == "203.0.113.9"

    def test_172_16_range_is_trusted(self):
        req = _make_request("172.31.255.255", forwarded_for="198.51.100.1")
        assert _real_ip(req) == "198.51.100.1"

    def test_192_168_range_is_trusted(self):
        req = _make_request("192.168.1.100", forwarded_for="198.51.100.2")
        assert _real_ip(req) == "198.51.100.2"
