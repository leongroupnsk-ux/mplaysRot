"""
/v1/domains — управление собственными доменами пользователя.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.links import CustomDomain
from app.models.user import User
from app.schemas.links import CustomDomainCreate, CustomDomainOut
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[CustomDomainOut])
async def list_domains(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(CustomDomain)
        .where(CustomDomain.user_id == current_user.id)
        .order_by(CustomDomain.created_at.desc())
    )
    return r.scalars().all()


@router.post("", response_model=CustomDomainOut, status_code=201)
async def add_domain(
    payload: CustomDomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    domain = payload.domain.lower().strip().rstrip("/")
    if not domain or " " in domain or len(domain) > 253:
        raise HTTPException(400, detail="Invalid domain name")

    # Check duplicate
    existing = await db.execute(select(CustomDomain).where(CustomDomain.domain == domain))
    if existing.scalar_one_or_none():
        raise HTTPException(409, detail="Domain already registered on this platform")

    record = CustomDomain(
        user_id=current_user.id,
        domain=domain,
        domain_type=payload.domain_type,
        status="pending_cname",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{domain_id}", status_code=204)
async def remove_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(CustomDomain).where(
            CustomDomain.id == uuid.UUID(domain_id),
            CustomDomain.user_id == current_user.id,
        )
    )
    record = r.scalar_one_or_none()
    if not record:
        raise HTTPException(404, detail="Domain not found")
    await db.delete(record)
    await db.commit()


@router.get("/cname-target")
async def cname_target():
    """Возвращает CNAME-запись, которую нужно прописать в DNS."""
    return {"cname": "domains.attribly.ru", "ttl": 300}
