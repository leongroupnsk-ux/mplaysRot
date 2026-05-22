"""
Нормализация и обогащение сырых событий из Kafka перед записью в ClickHouse.
"""
import hashlib
import json
from urllib.parse import urlparse


def normalize_click(raw: dict) -> dict | None:
    """
    Принимает сырое событие из топика attribly.clicks.
    Возвращает нормализованную строку для таблицы clicks или None если событие некорректное.
    """
    try:
        trax_id = raw.get("trax_id", "")
        if not trax_id:
            return None

        ip = raw.get("ip", "")
        ua = raw.get("user_agent", "")
        ts_str = raw.get("timestamp", "")

        # Обезличиваем IP через SHA-256
        ip_hash = hashlib.sha256(ip.encode()).hexdigest() if ip else ""

        # Visitor fingerprint: SHA-256(ip + ua + date) — повторные визиты в день считаются одним
        date_part = ts_str[:10] if ts_str else ""
        visitor_hash = hashlib.sha256(f"{ip}{ua}{date_part}".encode()).hexdigest()

        # Домен реферера
        referrer = raw.get("referrer", "")
        referrer_domain = _extract_domain(referrer)

        return {
            "event_id": raw.get("event_id", ""),
            "trax_id": trax_id,
            "campaign_id": raw.get("campaign_id", ""),
            "user_id": raw.get("user_id", ""),
            "visitor_hash": visitor_hash,
            "timestamp": ts_str,
            "ip_hash": ip_hash,
            "device_type": raw.get("device_type", "desktop"),
            "os": raw.get("os", ""),
            "browser": raw.get("browser", ""),
            "country": raw.get("country", ""),
            "region": raw.get("region", ""),
            "referrer_domain": referrer_domain,
            "ad_platform": raw.get("ad_platform", ""),
            "marketplace": raw.get("marketplace", ""),
        }
    except Exception:
        return None


def normalize_funnel_event(raw: dict) -> dict | None:
    """
    Принимает событие favourite/cart_add/cart_remove из топика attribly.events.
    """
    try:
        event_type = raw.get("event_type", "")
        if event_type not in ("favorite", "cart_add", "cart_remove"):
            return None

        trax_id = raw.get("trax_id", "")
        visitor_hash = raw.get("visitor_hash", "")
        if not trax_id and not visitor_hash:
            return None

        return {
            "event_id": raw.get("event_id", ""),
            "trax_id": trax_id,
            "campaign_id": raw.get("campaign_id", ""),
            "visitor_hash": visitor_hash,
            "event_type": event_type,
            "marketplace": raw.get("marketplace", ""),
            "product_id": raw.get("product_id", ""),
            "timestamp": raw.get("timestamp", ""),
        }
    except Exception:
        return None


def normalize_order(raw: dict) -> dict | None:
    """
    Принимает событие заказа из топика attribly.orders.
    """
    try:
        order_id = raw.get("order_id", "")
        if not order_id:
            return None

        return {
            "order_id": order_id,
            "marketplace": raw.get("marketplace", ""),
            "user_id": raw.get("user_id", ""),
            "product_id": raw.get("product_id", ""),
            "sku": raw.get("sku", ""),
            "quantity": int(raw.get("quantity", 1)),
            "order_amount": float(raw.get("order_amount", 0)),
            "currency": raw.get("currency", "RUB"),
            "order_status": raw.get("order_status", ""),
            "ordered_at": raw.get("ordered_at", ""),
            "delivered_at": raw.get("delivered_at", ""),
            "utm_trax_id": raw.get("utm_trax_id", ""),
        }
    except Exception:
        return None


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""
