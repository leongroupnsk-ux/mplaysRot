"""
/admin/domains — управление кастомными доменами (административный доступ).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.links import CustomDomain
from app.models.user import User
from app.schemas.links import AdminDomainOut, CustomDomainOut
from app.utils.deps import require_admin

router = APIRouter()


@router.get("", response_model=list[AdminDomainOut])
async def admin_list_domains(
    status: Optional[str] = Query(None),
    domain_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Список всех доменов на платформе с возможностью фильтрации."""
    q = select(CustomDomain).order_by(CustomDomain.created_at.desc())
    if status:
        q = q.where(CustomDomain.status == status)
    if domain_type:
        q = q.where(CustomDomain.domain_type == domain_type)
    q = q.limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.get("/{domain_id}", response_model=AdminDomainOut)
async def admin_get_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")
    return domain


@router.patch("/{domain_id}", response_model=CustomDomainOut)
async def admin_update_domain(
    domain_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Позволяет администратору вручную обновить статус, ssl_type, error_message, cname_verified.
    Полезно для ручного подтверждения/сброса доменов.
    """
    allowed_fields = {"status", "cname_verified", "ssl_type", "error_message"}
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")

    for k, v in payload.items():
        if k in allowed_fields:
            setattr(domain, k, v)

    await db.commit()
    await db.refresh(domain)
    return domain


@router.delete("/{domain_id}", status_code=204)
async def admin_delete_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")
    await db.delete(domain)
    await db.commit()


@router.post("/{domain_id}/verify", response_model=CustomDomainOut)
async def admin_verify_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Ручное подтверждение CNAME-записи администратором.
    В продакшне заменяется автоматическим воркером DNS-проверки.
    """
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")

    domain.cname_verified = True
    domain.status = "pending_ssl"
    domain.error_message = None
    await db.commit()
    await db.refresh(domain)
    return domain


@router.post("/{domain_id}/activate", response_model=CustomDomainOut)
async def admin_activate_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Активировать домен (CNAME + SSL подтверждены)."""
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")

    domain.cname_verified = True
    domain.status = "active"
    domain.error_message = None
    await db.commit()
    await db.refresh(domain)
    return domain


@router.post("/{domain_id}/suspend", response_model=CustomDomainOut)
async def admin_suspend_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Приостановить домен (нарушение ToS, неоплата и т.д.)."""
    try:
        did = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid domain_id")

    r = await db.execute(select(CustomDomain).where(CustomDomain.id == did))
    domain = r.scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail="Domain not found")

    domain.status = "suspended"
    await db.commit()
    await db.refresh(domain)
    return domain
