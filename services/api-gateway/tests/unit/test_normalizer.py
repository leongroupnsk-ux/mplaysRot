"""Unit tests for ETL normalizer (services/etl/normalizer.py)."""
import hashlib

from services.etl.normalizer import (
    normalize_click,
    normalize_order,
    normalize_funnel_event,
)


# ── normalize_click ───────────────────────────────────────────────────────────

def _click_raw(**overrides) -> dict:
    base = {
        "event_id": "evt-001",
        "trax_id": "ab12cd34",
        "campaign_id": "camp-001",
        "user_id": "user-001",
        "timestamp": "2026-04-15T12:00:00Z",
        "ip": "203.0.113.42",
        "user_agent": "Mozilla/5.0 (Linux; Android 13)",
        "device_type": "mobile",
        "os": "Android",
        "browser": "Chrome",
        "country": "RU",
        "region": "Москва",
        "referrer": "https://vk.com/ads",
        "ad_platform": "vk_ads",
        "marketplace": "ozon",
    }
    return {**base, **overrides}


def test_normalize_click_happy_path():
    result = normalize_click(_click_raw())
    assert result is not None
    assert result["trax_id"] == "ab12cd34"
    assert result["campaign_id"] == "camp-001"
    assert result["device_type"] == "mobile"
    assert result["marketplace"] == "ozon"


def test_normalize_click_ip_is_hashed():
    raw = _click_raw(ip="203.0.113.42")
    result = normalize_click(raw)
    assert result is not None
    expected_hash = hashlib.sha256("203.0.113.42".encode()).hexdigest()
    assert result["ip_hash"] == expected_hash
    assert "ip" not in result


def test_normalize_click_visitor_hash_includes_date():
    raw = _click_raw(ip="1.2.3.4", user_agent="UA", timestamp="2026-04-15T09:00:00Z")
    result = normalize_click(raw)
    assert result is not None
    expected = hashlib.sha256("1.2.3.42026-04-15UA".encode()).hexdigest()
    # Order: ip + ua + date (from normalizer: f"{ip}{ua}{date_part}")
    expected = hashlib.sha256(f"1.2.3.4UA2026-04-15".encode()).hexdigest()
    assert result["visitor_hash"] == expected


def test_normalize_click_referrer_domain_extracted():
    raw = _click_raw(referrer="https://vk.com/ads?q=1")
    result = normalize_click(raw)
    assert result is not None
    assert result["referrer_domain"] == "vk.com"


def test_normalize_click_empty_referrer():
    result = normalize_click(_click_raw(referrer=""))
    assert result is not None
    assert result["referrer_domain"] == ""


def test_normalize_click_missing_trax_id_returns_none():
    raw = _click_raw(trax_id="")
    assert normalize_click(raw) is None


def test_normalize_click_no_trax_id_key_returns_none():
    raw = _click_raw()
    del raw["trax_id"]
    assert normalize_click(raw) is None


def test_normalize_click_empty_ip_gives_empty_hash():
    result = normalize_click(_click_raw(ip=""))
    assert result is not None
    assert result["ip_hash"] == ""


# ── normalize_order ───────────────────────────────────────────────────────────

def _order_raw(**overrides) -> dict:
    base = {
        "order_id": "order-12345",
        "marketplace": "ozon",
        "user_id": "user-001",
        "product_id": "prod-999",
        "sku": "SKU-ABC",
        "quantity": 2,
        "order_amount": 3990.0,
        "currency": "RUB",
        "order_status": "confirmed",
        "ordered_at": "2026-04-15T14:00:00Z",
        "delivered_at": "",
        "utm_trax_id": "ab12cd34",
    }
    return {**base, **overrides}


def test_normalize_order_happy_path():
    result = normalize_order(_order_raw())
    assert result is not None
    assert result["order_id"] == "order-12345"
    assert result["quantity"] == 2
    assert result["order_amount"] == 3990.0
    assert result["utm_trax_id"] == "ab12cd34"


def test_normalize_order_quantity_coerced_to_int():
    result = normalize_order(_order_raw(quantity="3"))
    assert result is not None
    assert result["quantity"] == 3


def test_normalize_order_amount_coerced_to_float():
    result = normalize_order(_order_raw(order_amount="1500"))
    assert result is not None
    assert result["order_amount"] == 1500.0


def test_normalize_order_missing_order_id_returns_none():
    assert normalize_order(_order_raw(order_id="")) is None


def test_normalize_order_no_utm_trax_id_defaults_empty():
    raw = _order_raw()
    del raw["utm_trax_id"]
    result = normalize_order(raw)
    assert result is not None
    assert result["utm_trax_id"] == ""


def test_normalize_order_currency_defaults_rub():
    raw = _order_raw()
    del raw["currency"]
    result = normalize_order(raw)
    assert result is not None
    assert result["currency"] == "RUB"


# ── normalize_funnel_event ────────────────────────────────────────────────────

def _funnel_raw(**overrides) -> dict:
    base = {
        "event_id": "fevt-001",
        "event_type": "cart_add",
        "trax_id": "ab12cd34",
        "visitor_hash": "aabbcc",
        "campaign_id": "camp-001",
        "marketplace": "ozon",
        "product_id": "prod-999",
        "timestamp": "2026-04-15T13:00:00Z",
    }
    return {**base, **overrides}


def test_normalize_funnel_event_cart_add():
    result = normalize_funnel_event(_funnel_raw(event_type="cart_add"))
    assert result is not None
    assert result["event_type"] == "cart_add"


def test_normalize_funnel_event_favorite():
    result = normalize_funnel_event(_funnel_raw(event_type="favorite"))
    assert result is not None


def test_normalize_funnel_event_cart_remove():
    result = normalize_funnel_event(_funnel_raw(event_type="cart_remove"))
    assert result is not None


def test_normalize_funnel_event_invalid_type_returns_none():
    result = normalize_funnel_event(_funnel_raw(event_type="purchase"))
    assert result is None


def test_normalize_funnel_event_no_trax_and_no_visitor_returns_none():
    result = normalize_funnel_event(_funnel_raw(trax_id="", visitor_hash=""))
    assert result is None


def test_normalize_funnel_event_only_visitor_hash_is_ok():
    result = normalize_funnel_event(_funnel_raw(trax_id="", visitor_hash="aabbcc"))
    assert result is not None
