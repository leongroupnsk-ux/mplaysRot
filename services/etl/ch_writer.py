"""
Thread-safe ClickHouse writer с буферизацией.
Пишет батчами для эффективной вставки.
"""
import logging
import clickhouse_connect
from clickhouse_connect.driver import Client

from config import settings

log = logging.getLogger(__name__)


def get_client() -> Client:
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_db,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )


def insert_clicks(client: Client, rows: list[dict]) -> None:
    if not rows:
        return
    data = [
        [
            r["event_id"],
            r["trax_id"],
            r.get("campaign_id", ""),
            r.get("user_id", ""),
            r.get("visitor_hash", ""),
            r["timestamp"],
            r.get("ip_hash", ""),
            r.get("device_type", "desktop"),
            r.get("os", ""),
            r.get("browser", ""),
            r.get("country", ""),
            r.get("region", ""),
            r.get("referrer_domain", ""),
            r.get("ad_platform", ""),
            r.get("marketplace", ""),
        ]
        for r in rows
    ]
    client.insert(
        "clicks",
        data,
        column_names=[
            "event_id", "trax_id", "campaign_id", "user_id", "visitor_hash",
            "ts", "ip_hash", "device_type", "os", "browser",
            "country", "region", "referrer_domain", "ad_platform", "marketplace",
        ],
    )
    log.info("Inserted %d clicks into ClickHouse", len(rows))


def insert_funnel_events(client: Client, rows: list[dict]) -> None:
    if not rows:
        return
    data = [
        [
            r["event_id"],
            r.get("trax_id", ""),
            r.get("campaign_id", ""),
            r.get("visitor_hash", ""),
            r.get("event_type", ""),
            r.get("marketplace", ""),
            r.get("product_id", ""),
            r["timestamp"],
        ]
        for r in rows
    ]
    client.insert(
        "funnel_events",
        data,
        column_names=[
            "event_id", "trax_id", "campaign_id", "visitor_hash",
            "event_type", "marketplace", "product_id", "ts",
        ],
    )
    log.info("Inserted %d funnel events into ClickHouse", len(rows))


def insert_orders(client: Client, rows: list[dict]) -> None:
    if not rows:
        return
    data = [
        [
            r["order_id"],
            r.get("marketplace", ""),
            r.get("user_id", ""),
            r.get("product_id", ""),
            r.get("sku", ""),
            int(r.get("quantity", 1)),
            float(r.get("order_amount", 0)),
            r.get("currency", "RUB"),
            r.get("order_status", ""),
            r.get("ordered_at", ""),
            r.get("delivered_at", ""),
        ]
        for r in rows
    ]
    client.insert(
        "marketplace_orders",
        data,
        column_names=[
            "order_id", "marketplace", "user_id", "product_id", "sku",
            "quantity", "order_amount", "currency", "order_status",
            "ordered_at", "delivered_at",
        ],
    )
    log.info("Inserted %d orders into ClickHouse", len(rows))
