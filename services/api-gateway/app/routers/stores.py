from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.models.catalog import Store
from app.schemas.catalog import StoreResponse
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[StoreResponse])
async def list_stores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Store)
        .where(Store.user_id == current_user.id, Store.is_active.is_(True))
        .order_by(Store.created_at)
    )
    return [
        StoreResponse(
            id=str(s.id),
            connection_id=str(s.marketplace_connection_id),
            provider=s.provider,
            external_store_id=s.external_store_id,
            name=s.name,
            logo_url=s.logo_url,
            is_active=s.is_active,
            last_sync_at=s.last_sync_at,
            created_at=s.created_at,
        )
        for s in result.scalars().all()
    ]
