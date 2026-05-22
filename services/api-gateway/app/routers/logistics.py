"""
/logistics — остатки по складам WB в реальном времени.
Проксирует данные из WB Statistics API и Marketplace API.
Кэширует ответы в Redis для обхода rate-limit WB (429).
"""
import json
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.db.redis import get_redis
from app.models.connections import MarketplaceConnection
from app.models.user import User
from app.services.platform_settings import get_platform_setting
from app.utils.crypto import decrypt_token
from app.utils.deps import get_current_user

router = APIRouter()

# TTL кэша: остатки меняются редко, достаточно 90 секунд
STOCKS_CACHE_TTL = 90
# TTL кэша складов: очень редко меняются
WAREHOUSES_CACHE_TTL = 300


async def _get_wb_connection(db: AsyncSession, user: User) -> MarketplaceConnection:
    r = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.user_id == user.id,
            MarketplaceConnection.marketplace == "wildberries",
            MarketplaceConnection.status == "active",
        ).limit(1)
    )
    conn = r.scalars().first()
    if not conn:
        raise HTTPException(404, detail="No active Wildberries connection found")
    return conn


@router.get("/stocks")
async def get_wb_stocks(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает остатки из WB Statistics API (/api/v1/supplier/stocks).
    Каждая запись = один баркод (размер) × склад.
    Результат кэшируется в Redis на 90 секунд; при 429 от WB возвращает
    stale-данные из кэша (если есть) или ошибку 429 с Retry-After.
    """
    conn = await _get_wb_connection(db, current_user)
    # Платформенный сервисный ключ (из admin-настроек) имеет приоритет над ключом пользователя
    platform_key = await get_platform_setting("wb_service_key", db)
    api_key = platform_key or decrypt_token(conn.api_key_enc)

    cache_key = f"wb:stocks:{current_user.id}"
    redis = get_redis()

    # ── Проверяем кэш ────────────────────────────────────────────────────
    try:
        cached = await redis.get(cache_key)
        if cached:
            response.headers["X-Cache"] = "HIT"
            return JSONResponse(content=json.loads(cached))
    except Exception:
        pass  # Redis недоступен — идём напрямую

    date_from = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        "%Y-%m-%dT00:00:00"
    )

    # ── Запрос к WB ──────────────────────────────────────────────────────
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            "https://statistics-api.wildberries.ru/api/v1/supplier/stocks",
            params={"dateFrom": date_from},
            headers={"Authorization": api_key},
        )

    if resp.status_code == 401:
        raise HTTPException(401, detail="WB API key is invalid or expired")

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        # Возвращаем stale-данные из кэша (с пометкой), если они есть
        try:
            stale = await redis.get(f"{cache_key}:stale")
            if stale:
                response.headers["X-Cache"] = "STALE"
                response.headers["X-RateLimit-RetryAfter"] = str(retry_after)
                return JSONResponse(
                    content=json.loads(stale),
                    headers={
                        "X-Cache": "STALE",
                        "X-RateLimit-RetryAfter": str(retry_after),
                    },
                )
        except Exception:
            pass
        raise HTTPException(
            429,
            detail=f"WB API rate limit exceeded. Повторите через {retry_after} сек.",
            headers={"Retry-After": str(retry_after)},
        )

    if resp.status_code != 200:
        raise HTTPException(502, detail=f"WB API error: {resp.status_code}")

    data = resp.json()

    # ── Сохраняем в кэш ──────────────────────────────────────────────────
    try:
        serialized = json.dumps(data)
        await redis.setex(cache_key, STOCKS_CACHE_TTL, serialized)
        # Stale-кэш живёт дольше — на случай длительного rate-limit
        await redis.setex(f"{cache_key}:stale", STOCKS_CACHE_TTL * 10, serialized)
    except Exception:
        pass  # не критично — вернём данные без кэша

    response.headers["X-Cache"] = "MISS"
    return data


@router.get("/warehouses")
async def get_wb_warehouses(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает список складов продавца из WB Marketplace API.
    Результат кэшируется на 300 секунд.
    """
    conn = await _get_wb_connection(db, current_user)
    platform_key = await get_platform_setting("wb_service_key", db)
    api_key = platform_key or decrypt_token(conn.api_key_enc)

    cache_key = f"wb:warehouses:{current_user.id}"
    redis = get_redis()

    # ── Проверяем кэш ────────────────────────────────────────────────────
    try:
        cached = await redis.get(cache_key)
        if cached:
            response.headers["X-Cache"] = "HIT"
            return JSONResponse(content=json.loads(cached))
    except Exception:
        pass

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://marketplace-api.wildberries.ru/api/v3/warehouses",
            headers={"Authorization": api_key},
        )

    if resp.status_code == 401:
        raise HTTPException(401, detail="WB API key is invalid or expired")

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        try:
            stale = await redis.get(f"{cache_key}:stale")
            if stale:
                return JSONResponse(
                    content=json.loads(stale),
                    headers={
                        "X-Cache": "STALE",
                        "X-RateLimit-RetryAfter": str(retry_after),
                    },
                )
        except Exception:
            pass
        raise HTTPException(
            429,
            detail=f"WB API rate limit exceeded. Повторите через {retry_after} сек.",
            headers={"Retry-After": str(retry_after)},
        )

    if resp.status_code != 200:
        raise HTTPException(502, detail=f"WB API error: {resp.status_code}")

    data = resp.json()

    try:
        serialized = json.dumps(data)
        await redis.setex(cache_key, WAREHOUSES_CACHE_TTL, serialized)
        await redis.setex(f"{cache_key}:stale", WAREHOUSES_CACHE_TTL * 6, serialized)
    except Exception:
        pass

    response.headers["X-Cache"] = "MISS"
    return data
