"""
Incoming webhook handlers for Telegram Ads and Messenger MAX.

Both platforms push ad-stat events in real time. We validate the
secret/signature, map the payload to ClickHouse schema, and insert.
"""
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import settings
from app.db.clickhouse import get_clickhouse

router = APIRouter()
log = logging.getLogger(__name__)


# ── Telegram Ads ──────────────────────────────────────────────────────────────

@router.post("/telegram", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_secret: str = Header(..., alias="X-Telegram-Secret"),
    ch=Depends(get_clickhouse),
):
    """Incoming events from Telegram Ads (click + conversion stats)."""
    _verify_telegram_secret(x_telegram_secret)

    body: dict[str, Any] = await request.json()
    events = body if isinstance(body, list) else [body]
    click_rows, stat_rows = [], []

    for ev in events:
        ev_type = ev.get("type", "click")
        if ev_type == "click":
            click_rows.append(_telegram_to_click_row(ev))
        elif ev_type == "stats":
            stat_rows.append(_telegram_to_stat_row(ev))

    if click_rows:
        ch.insert("clicks", click_rows, column_names=[
            "event_id", "trax_id", "campaign_id", "user_id", "visitor_hash",
            "ts", "ip_hash", "device_type", "os", "browser",
            "country", "region", "referrer_domain", "ad_platform", "marketplace",
        ])

    if stat_rows:
        ch.insert("ad_stats", stat_rows, column_names=[
            "stat_date", "ad_platform", "user_id", "campaign_id",
            "external_campaign_id", "external_ad_id", "ad_name",
            "impressions", "clicks", "spend", "currency", "ctr", "cpc",
        ])

    log.info("telegram_webhook: %d clicks, %d stat rows", len(click_rows), len(stat_rows))
    return {"accepted": len(click_rows) + len(stat_rows)}


# ── Messenger MAX ─────────────────────────────────────────────────────────────

@router.post("/messenger-max", status_code=status.HTTP_200_OK)
async def messenger_max_webhook(
    request: Request,
    x_max_signature: str = Header(..., alias="X-Max-Signature"),
    ch=Depends(get_clickhouse),
):
    """Incoming events from Messenger MAX (HMAC-SHA256 signed)."""
    raw_body = await request.body()
    _verify_max_signature(raw_body, x_max_signature)

    import json
    body: dict[str, Any] = json.loads(raw_body)
    events = body if isinstance(body, list) else [body]
    click_rows, stat_rows = [], []

    for ev in events:
        ev_type = ev.get("type", "click")
        if ev_type == "click":
            click_rows.append(_max_to_click_row(ev))
        elif ev_type == "stats":
            stat_rows.append(_max_to_stat_row(ev))

    if click_rows:
        ch.insert("clicks", click_rows, column_names=[
            "event_id", "trax_id", "campaign_id", "user_id", "visitor_hash",
            "ts", "ip_hash", "device_type", "os", "browser",
            "country", "region", "referrer_domain", "ad_platform", "marketplace",
        ])

    if stat_rows:
        ch.insert("ad_stats", stat_rows, column_names=[
            "stat_date", "ad_platform", "user_id", "campaign_id",
            "external_campaign_id", "external_ad_id", "ad_name",
            "impressions", "clicks", "spend", "currency", "ctr", "cpc",
        ])

    log.info("messenger_max_webhook: %d clicks, %d stat rows", len(click_rows), len(stat_rows))
    return {"accepted": len(click_rows) + len(stat_rows)}


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _verify_telegram_secret(provided: str) -> None:
    expected = settings.telegram_webhook_secret
    if not expected:
        return  # secret not configured — skip in dev
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")


def _verify_max_signature(body: bytes, provided: str) -> None:
    secret = settings.messenger_max_webhook_secret
    if not secret:
        return  # skip in dev
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid HMAC signature")


# ── Row mappers ───────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _telegram_to_click_row(ev: dict) -> list:
    return [
        ev.get("event_id") or str(uuid.uuid4()),
        ev.get("trax_id", ""),
        ev.get("campaign_id", ""),
        ev.get("user_id", ""),
        ev.get("visitor_hash", ""),
        ev.get("ts") or _now_utc(),
        ev.get("ip_hash", ""),
        ev.get("device_type", ""),
        ev.get("os", ""),
        ev.get("browser", ""),
        ev.get("country", ""),
        ev.get("region", ""),
        ev.get("referrer_domain", ""),
        "telegram_ads",
        ev.get("marketplace", ""),
    ]


def _telegram_to_stat_row(ev: dict) -> list:
    impressions = int(ev.get("impressions", 0))
    clicks = int(ev.get("clicks", 0))
    spend = float(ev.get("spend", 0))
    ctr = clicks / impressions if impressions > 0 else 0.0
    cpc = spend / clicks if clicks > 0 else 0.0
    return [
        ev.get("stat_date") or _now_utc().date(),
        "telegram_ads",
        ev.get("user_id", ""),
        ev.get("campaign_id", ""),
        ev.get("external_campaign_id", ""),
        ev.get("external_ad_id", ""),
        ev.get("ad_name", ""),
        impressions,
        clicks,
        spend,
        ev.get("currency", "RUB"),
        ctr,
        cpc,
    ]


def _max_to_click_row(ev: dict) -> list:
    return [
        ev.get("event_id") or str(uuid.uuid4()),
        ev.get("trax_id", ""),
        ev.get("campaign_id", ""),
        ev.get("user_id", ""),
        ev.get("visitor_hash", ""),
        ev.get("ts") or _now_utc(),
        ev.get("ip_hash", ""),
        ev.get("device_type", ""),
        ev.get("os", ""),
        ev.get("browser", ""),
        ev.get("country", ""),
        ev.get("region", ""),
        ev.get("referrer_domain", ""),
        "messenger_max",
        ev.get("marketplace", ""),
    ]


def _max_to_stat_row(ev: dict) -> list:
    impressions = int(ev.get("impressions", 0))
    clicks = int(ev.get("clicks", 0))
    spend = float(ev.get("spend", 0))
    ctr = clicks / impressions if impressions > 0 else 0.0
    cpc = spend / clicks if clicks > 0 else 0.0
    return [
        ev.get("stat_date") or _now_utc().date(),
        "messenger_max",
        ev.get("user_id", ""),
        ev.get("campaign_id", ""),
        ev.get("external_campaign_id", ""),
        ev.get("external_ad_id", ""),
        ev.get("ad_name", ""),
        impressions,
        clicks,
        spend,
        ev.get("currency", "RUB"),
        ctr,
        cpc,
    ]
