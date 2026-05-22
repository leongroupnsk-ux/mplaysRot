import json
import uuid
from datetime import datetime, timezone

from fastapi import Request
from user_agents import parse as parse_ua

from app.kafka_producer import produce_event
from app.redis_client import get_redis


async def resolve_destination(trax_id: str) -> str | None:
    redis = get_redis()
    return await redis.get(f"trax:dest:{trax_id}")


async def record_click(trax_id: str, request: Request) -> None:
    ua_string = request.headers.get("user-agent", "")
    ua = parse_ua(ua_string)
    redis = get_redis()

    # Обогащаем событие метаданными кампании из Redis (записываются при создании ссылки)
    meta = await redis.hgetall(f"trax:meta:{trax_id}")

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "click",
        "trax_id": trax_id,
        "campaign_id": meta.get("campaign_id", ""),
        "user_id": meta.get("user_id", ""),
        "ad_platform": meta.get("ad_platform", ""),
        "marketplace": meta.get("marketplace", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip": _extract_ip(request),
        "user_agent": ua_string,
        "device_type": "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop",
        "os": ua.os.family,
        "browser": ua.browser.family,
        "referrer": request.headers.get("referer", ""),
    }

    await produce_event(topic="attribly.clicks", key=trax_id, value=json.dumps(event))


def _extract_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""
