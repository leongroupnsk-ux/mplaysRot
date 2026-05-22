import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.connections import AdPlatformConnection, MarketplaceConnection
from app.models.user import User
from app.schemas.connections import (
    AdConnectionCreate, AdConnectionResponse,
    MarketplaceConnectionCreate, MarketplaceConnectionResponse, MarketplaceConnectionUpdate,
)
from app.utils.crypto import encrypt_token
from app.utils.deps import get_current_user

router = APIRouter()

_ALLOWED_AD_PLATFORMS = {"telegram_ads", "vk_ads", "yandex_direct", "messenger_max", "mytarget"}
_ALLOWED_MARKETPLACES = {"ozon", "wildberries", "yandex_market", "aliexpress"}


# ── Ad platforms ──────────────────────────────────────────────────────────────

@router.get("/ad-platforms", response_model=list[AdConnectionResponse])
async def list_ad_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AdPlatformConnection)
        .where(
            AdPlatformConnection.user_id == current_user.id,
            AdPlatformConnection.is_active.is_(True),
        )
        .order_by(AdPlatformConnection.created_at.desc())
    )
    rows = result.scalars().all()
    return [_ad_response(r) for r in rows]


@router.post("/ad-platforms", response_model=AdConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_ad_connection(
    payload: AdConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.platform not in _ALLOWED_AD_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported platform. Allowed: {sorted(_ALLOWED_AD_PLATFORMS)}",
        )

    conn = AdPlatformConnection(
        user_id=current_user.id,
        platform=payload.platform,
        access_token_enc=encrypt_token(payload.access_token),
        refresh_token_enc=encrypt_token(payload.refresh_token) if payload.refresh_token else None,
        account_id=payload.account_id,
        is_active=True,
        status="active",
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return _ad_response(conn)


@router.delete("/ad-platforms/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AdPlatformConnection).where(
            AdPlatformConnection.id == uuid.UUID(connection_id),
            AdPlatformConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    conn.is_active = False
    await db.commit()


# ── Marketplaces ──────────────────────────────────────────────────────────────

@router.get("/marketplaces", response_model=list[MarketplaceConnectionResponse])
async def list_marketplace_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MarketplaceConnection)
        .where(
            MarketplaceConnection.user_id == current_user.id,
            MarketplaceConnection.is_active.is_(True),
        )
        .order_by(MarketplaceConnection.created_at.desc())
    )
    rows = result.scalars().all()
    return [_mp_response(r) for r in rows]


@router.post("/marketplaces", response_model=MarketplaceConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_marketplace_connection(
    payload: MarketplaceConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.marketplace not in _ALLOWED_MARKETPLACES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported marketplace. Allowed: {sorted(_ALLOWED_MARKETPLACES)}",
        )

    conn = MarketplaceConnection(
        user_id=current_user.id,
        marketplace=payload.marketplace,
        api_key_enc=encrypt_token(payload.api_key),
        service_key_enc=encrypt_token(payload.service_key) if payload.service_key else None,
        client_id=payload.client_id,
        is_active=True,
        status="active",
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return _mp_response(conn)


@router.patch("/marketplaces/{connection_id}", response_model=MarketplaceConnectionResponse)
async def update_marketplace_connection(
    connection_id: str,
    payload: MarketplaceConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.id == uuid.UUID(connection_id),
            MarketplaceConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    if payload.api_key is not None:
        conn.api_key_enc = encrypt_token(payload.api_key)
    if payload.service_key is not None:
        conn.service_key_enc = encrypt_token(payload.service_key)
    await db.commit()
    await db.refresh(conn)
    return _mp_response(conn)


@router.delete("/marketplaces/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marketplace_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.id == uuid.UUID(connection_id),
            MarketplaceConnection.user_id == current_user.id,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    conn.is_active = False
    await db.commit()


# ── Serializers ───────────────────────────────────────────────────────────────

def _ad_response(conn: AdPlatformConnection) -> AdConnectionResponse:
    return AdConnectionResponse(
        id=str(conn.id),
        platform=conn.platform,
        account_id=conn.account_id,
        account_name=conn.account_name,
        is_active=conn.is_active,
        last_synced_at=conn.last_synced_at,
    )


def _mp_response(conn: MarketplaceConnection) -> MarketplaceConnectionResponse:
    return MarketplaceConnectionResponse(
        id=str(conn.id),
        marketplace=conn.marketplace,
        client_id=conn.client_id,
        marketplace_name=conn.marketplace_name,
        is_active=conn.is_active,
        last_synced_at=conn.last_synced_at,
        has_service_key=bool(conn.service_key_enc),
    )
