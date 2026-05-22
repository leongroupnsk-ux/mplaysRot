"""
Общие утилиты для Feature Engineering.
"""
import hashlib
from datetime import datetime, timezone


def hours_between(ts1: str, ts2: str) -> float:
    """Количество часов между двумя ISO-строками."""
    dt1 = datetime.fromisoformat(ts1.replace("Z", "+00:00"))
    dt2 = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
    return abs((dt2 - dt1).total_seconds()) / 3600


def geo_match(region_click: str, region_order: str) -> int:
    return int(bool(region_click and region_order and region_click == region_order))


def device_match(device_click: str, device_order: str) -> int:
    return int(bool(device_click and device_order and device_click == device_order))


def product_match(product_click: str, product_order: str) -> int:
    return int(bool(product_click and product_order and product_click == product_order))


def stable_hash(value: str) -> int:
    """Детерминированный числовой хеш строки для категориальных признаков."""
    return int(hashlib.md5(value.encode()).hexdigest(), 16) % (10 ** 8)
