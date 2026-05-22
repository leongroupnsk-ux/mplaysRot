"""
/integrations — управление подключениями к маркетплейсам и рекламным кабинетам.

Унифицирует ad_platform_connections и marketplace_connections в один REST-ресурс.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.models.connections import AdPlatformConnection, MarketplaceConnection
from app.models.catalog import Store
from app.schemas.integrations import (
    MarketplaceConnectRequest, AdConnectRequest,
    IntegrationResponse, ValidateResponse,
)
from app.utils.crypto import encrypt_token, decrypt_token
from app.utils.deps import get_current_user

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _mp_to_response(c: MarketplaceConnection) -> IntegrationResponse:
    return IntegrationResponse(
        id=str(c.id),
        type="marketplace",
        provider=c.marketplace,
        account_name=c.marketplace_name,
        status=c.status,
        last_synced_at=c.last_synced_at,
        created_at=c.created_at,
    )


def _ad_to_response(c: AdPlatformConnection) -> IntegrationResponse:
    return IntegrationResponse(
        id=str(c.id),
        type="ad_platform",
        provider=c.platform,
        account_name=c.account_name,
        status=c.status,
        last_synced_at=c.last_synced_at,
        created_at=c.created_at,
    )


# ── GET /integrations ─────────────────────────────────────────────────────────

@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mp_result = await db.execute(
        select(MarketplaceConnection)
        .where(MarketplaceConnection.user_id == current_user.id)
        .order_by(MarketplaceConnection.created_at)
    )
    ad_result = await db.execute(
        select(AdPlatformConnection)
        .where(AdPlatformConnection.user_id == current_user.id)
        .order_by(AdPlatformConnection.created_at)
    )
    mp = [_mp_to_response(c) for c in mp_result.scalars().all()]
    ad = [_ad_to_response(c) for c in ad_result.scalars().all()]
    return mp + ad


# ── POST /integrations/marketplace ────────────────────────────────────────────

@router.post("/marketplace", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect_marketplace(
    payload: MarketplaceConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── Проверка дублей: запрещаем подключать один маркетплейс дважды ────────
    existing = (await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.user_id == current_user.id,
            MarketplaceConnection.marketplace == payload.provider,
            MarketplaceConnection.is_active.is_(True),
        ).limit(1)
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Маркетплейс «{payload.provider}» уже подключён. "
                   "Удалите существующее подключение перед добавлением нового.",
        )

    conn = MarketplaceConnection(
        user_id=current_user.id,
        marketplace=payload.provider,
        api_key_enc=encrypt_token(payload.api_key),
        client_id=payload.client_id,
        seller_id=payload.seller_id,
        status="pending",
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    # Валидируем и подтягиваем имя аккаунта
    ok, msg = await _validate_marketplace(conn)
    conn.status = "active" if ok else "error"
    if ok:
        conn.marketplace_name = await _fetch_marketplace_name(payload.provider, payload.api_key)
        await _ensure_store(db, conn)
    await db.commit()
    await db.refresh(conn)

    return _mp_to_response(conn)


# ── POST /integrations/ad ─────────────────────────────────────────────────────

@router.post("/ad", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect_ad_platform(
    payload: AdConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = AdPlatformConnection(
        user_id=current_user.id,
        platform=payload.provider,
        access_token_enc=encrypt_token(payload.access_token),
        refresh_token_enc=encrypt_token(payload.refresh_token) if payload.refresh_token else None,
        account_id=payload.account_id,
        account_name=payload.account_name,
        status="pending",
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    ok, _ = await _validate_ad(conn)
    conn.status = "active" if ok else "error"
    await db.commit()
    await db.refresh(conn)

    return _ad_to_response(conn)


# ── DELETE /integrations/{id} ─────────────────────────────────────────────────

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = uuid.UUID(integration_id)

    # Try marketplace first
    r = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.id == uid,
            MarketplaceConnection.user_id == current_user.id,
        )
    )
    if mp := r.scalar_one_or_none():
        await db.delete(mp)
        await db.commit()
        return

    # Then ad platform
    r = await db.execute(
        select(AdPlatformConnection).where(
            AdPlatformConnection.id == uid,
            AdPlatformConnection.user_id == current_user.id,
        )
    )
    if ad := r.scalar_one_or_none():
        await db.delete(ad)
        await db.commit()
        return

    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Integration not found")


# ── POST /integrations/{id}/validate ─────────────────────────────────────────

@router.post("/{integration_id}/validate", response_model=ValidateResponse)
async def validate_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = uuid.UUID(integration_id)

    r = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.id == uid,
            MarketplaceConnection.user_id == current_user.id,
        )
    )
    if mp := r.scalar_one_or_none():
        ok, msg = await _validate_marketplace(mp)
        mp.status = "active" if ok else "error"
        if ok:
            await _ensure_store(db, mp)
        mp.last_synced_at = datetime.now(timezone.utc)
        await db.commit()
        return ValidateResponse(ok=ok, message=msg)

    r = await db.execute(
        select(AdPlatformConnection).where(
            AdPlatformConnection.id == uid,
            AdPlatformConnection.user_id == current_user.id,
        )
    )
    if ad := r.scalar_one_or_none():
        ok, msg = await _validate_ad(ad)
        ad.status = "active" if ok else "error"
        ad.last_synced_at = datetime.now(timezone.utc)
        await db.commit()
        return ValidateResponse(ok=ok, message=msg)

    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Integration not found")


# ── internal ──────────────────────────────────────────────────────────────────

async def _fetch_marketplace_name(provider: str, api_key: str) -> str | None:
    """Получает отображаемое имя аккаунта (продавца) из API маркетплейса."""
    try:
        import httpx
        if provider == "wildberries":
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://common-api.wildberries.ru/api/v1/seller-info",
                    headers={"Authorization": api_key},
                )
            if r.status_code == 200:
                data = r.json()
                trade = data.get("tradeMark")
                legal = data.get("name")
                if trade and legal and trade != legal:
                    return f"{trade} · {legal}"
                return trade or legal
            # 429 — rate limit, вернём None, имя можно будет показать при след. синхронизации
        elif provider == "ozon":
            pass
    except Exception:
        pass
    return None


async def _validate_marketplace(conn: MarketplaceConnection) -> tuple[bool, str]:
    try:
        import sys, os
        _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if _ROOT not in sys.path:
            sys.path.insert(0, _ROOT)

        from app.utils.crypto import decrypt_token
        from app.services.catalog import _build_connector
        connector = _build_connector(conn)
        return await connector.test_connection()
    except Exception as exc:
        return False, f"Ошибка: {exc}"


async def _validate_ad(conn: AdPlatformConnection) -> tuple[bool, str]:
    try:
        import sys, os
        _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if _ROOT not in sys.path:
            sys.path.insert(0, _ROOT)

        from app.utils.crypto import decrypt_token
        access_token = decrypt_token(conn.access_token_enc)

        platform = conn.platform
        if platform == "yandex_direct":
            from services.ingestion.connectors.yandex_direct.connector import YandexDirectConnector
            c = YandexDirectConnector(access_token=access_token, client_login=conn.account_id or "")
        elif platform == "vk_ads":
            from services.ingestion.connectors.vk_ads.connector import VKAdsConnector
            c = VKAdsConnector(access_token=access_token, account_id=conn.account_id or "")
        elif platform == "vk_blogger":
            from services.ingestion.connectors.vk_blogger.connector import VKBloggerConnector
            c = VKBloggerConnector(access_token=access_token, owner_ids=[])
        elif platform == "telegram_ads":
            from services.ingestion.connectors.telegram_ads.connector import TelegramAdsConnector
            c = TelegramAdsConnector(access_token=access_token)
        elif platform == "messenger_max":
            from services.ingestion.connectors.messenger_max.connector import MessengerMaxConnector
            c = MessengerMaxConnector(access_token=access_token, webhook_secret="")
        else:
            return False, f"Неизвестная платформа: {platform}"

        return await c.test_connection()
    except Exception as exc:
        return False, f"Ошибка: {exc}"


async def _ensure_store(db: AsyncSession, conn: MarketplaceConnection) -> None:
    """Создаёт Store если его ещё нет для этого подключения."""
    existing = await db.execute(
        select(Store).where(Store.marketplace_connection_id == conn.id)
    )
    if existing.scalar_one_or_none():
        return

    name = conn.marketplace_name or conn.marketplace
    external_id = conn.seller_id or conn.client_id or str(conn.id)

    store = Store(
        user_id=conn.user_id,
        marketplace_connection_id=conn.id,
        provider=conn.marketplace,
        external_store_id=external_id,
        name=name,
        is_active=True,
    )
    db.add(store)
    # commit handled by caller
