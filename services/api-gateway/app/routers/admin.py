"""
Admin panel API — all endpoints require role=admin JWT.

POST  /admin/auth/login        — password + TOTP → admin JWT
GET   /admin/auth/totp-setup   — generate TOTP secret for an admin account
GET   /admin/stats             — platform-wide counters
GET   /admin/users             — paginated user list
GET   /admin/users/{id}        — single user
PATCH /admin/users/{id}        — update role / is_active / full_name
"""
from __future__ import annotations

import pyotp
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.audit import AdminAuditLog
from app.models.billing import PromoCode, SubscriptionPlan, UserSubscription
from app.models.segments import SegmentUpload
from app.models.user import User
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminStatsOut,
    AdminTotpSetupOut,
    AdminUserOut,
    AdminUserPatch,
)
from app.schemas.billing import (
    AdminAuditLogOut,
    AdminPlanOut,
    AdminPromoOut,
    AssignPlanRequest,
    PlanCreateRequest,
    PlanUpdateRequest,
    PromoCreateRequest,
)
from app.services.platform_settings import (
    get_platform_setting, set_platform_setting, delete_platform_setting
)
from app.utils.deps import require_admin
from app.utils.jwt import create_access_token

router = APIRouter()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=AdminTokenResponse)
async def admin_login(
    body: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminTokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active or user.role != "admin":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if not _pwd.verify(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if user.totp_secret:
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(body.totp_code, valid_window=1):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid TOTP code")

    token = create_access_token(str(user.id))
    return AdminTokenResponse(access_token=token)


@router.get("/auth/totp-setup", response_model=AdminTotpSetupOut)
async def admin_totp_setup(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminTotpSetupOut:
    """Generate a new TOTP secret for the calling admin and persist it."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_admin.email, issuer_name="Attribly Admin")

    current_admin.totp_secret = secret
    await db.commit()

    return AdminTotpSetupOut(
        totp_secret=secret,
        totp_uri=uri,
        message="Scan the QR-code with your authenticator app, then verify with a code.",
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsOut)
async def admin_stats(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsOut:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active = (await db.execute(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    )).scalar_one()
    admins = (await db.execute(
        select(func.count()).select_from(User).where(User.role == "admin")
    )).scalar_one()
    new_30d = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= cutoff)
    )).scalar_one()

    return AdminStatsOut(
        total_users=total,
        active_users=active,
        admin_users=admins,
        users_last_30d=new_30d,
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
) -> list[AdminUserOut]:
    q = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    if search:
        like = f"%{search}%"
        q = q.where(User.email.ilike(like) | User.full_name.ilike(like))
    rows = (await db.execute(q)).scalars().all()
    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            totp_enabled=bool(u.totp_secret),
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in rows
    ]


@router.get("/users/{user_id}", response_model=AdminUserOut)
async def get_user(
    user_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        totp_enabled=bool(user.totp_secret),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def patch_user(
    user_id: str,
    body: AdminUserPatch,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    _ALLOWED_ROLES = {"analyst", "owner", "admin"}
    if body.role is not None:
        if body.role not in _ALLOWED_ROLES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"role must be one of {_ALLOWED_ROLES}")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.full_name is not None:
        user.full_name = body.full_name

    user.updated_at = datetime.now(timezone.utc)
    await _audit(db, current_admin, "change_role", "user", str(user_id),
                 {"role": body.role, "is_active": body.is_active})
    await db.commit()

    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        totp_enabled=bool(user.totp_secret),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ── Billing: plans ────────────────────────────────────────────────────────────

@router.get("/billing/plans", response_model=list[AdminPlanOut])
async def admin_list_plans(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPlanOut]:
    rows = (await db.execute(
        select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order)
    )).scalars().all()
    return [AdminPlanOut.model_validate(r) for r in rows]


@router.post("/billing/plans", response_model=AdminPlanOut, status_code=status.HTTP_201_CREATED)
async def admin_create_plan(
    body: PlanCreateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPlanOut:
    plan = SubscriptionPlan(**body.model_dump())
    db.add(plan)
    await db.flush()
    await _audit(db, current_admin, "create_plan", "plan", str(plan.id), body.model_dump())
    await db.commit()
    await db.refresh(plan)
    return AdminPlanOut.model_validate(plan)


@router.patch("/billing/plans/{plan_id}", response_model=AdminPlanOut)
async def admin_update_plan(
    plan_id: str,
    body: PlanUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPlanOut:
    import uuid as _uuid
    plan = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == _uuid.UUID(plan_id))
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(plan, k, v)
    plan.updated_at = datetime.now(timezone.utc)
    await _audit(db, current_admin, "update_plan", "plan", plan_id, body.model_dump(exclude_none=True))
    await db.commit()
    await db.refresh(plan)
    return AdminPlanOut.model_validate(plan)


@router.delete("/billing/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_plan(
    plan_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    import uuid as _uuid
    plan = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == _uuid.UUID(plan_id))
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    plan.is_active = False  # soft-delete
    await _audit(db, current_admin, "delete_plan", "plan", plan_id, {"slug": plan.slug})
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Billing: promo codes ──────────────────────────────────────────────────────

@router.get("/billing/promos", response_model=list[AdminPromoOut])
async def admin_list_promos(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPromoOut]:
    rows = (await db.execute(
        select(PromoCode).order_by(PromoCode.created_at.desc())
    )).scalars().all()
    return [AdminPromoOut.model_validate(r) for r in rows]


@router.post("/billing/promos", response_model=AdminPromoOut, status_code=status.HTTP_201_CREATED)
async def admin_create_promo(
    body: PromoCreateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPromoOut:
    promo = PromoCode(**body.model_dump(), code=body.code.upper())
    db.add(promo)
    await db.flush()
    await _audit(db, current_admin, "create_promo", "promo", str(promo.id),
                 {"code": promo.code, "discount_pct": promo.discount_pct})
    await db.commit()
    await db.refresh(promo)
    return AdminPromoOut.model_validate(promo)


@router.delete("/billing/promos/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_promo(
    promo_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    import uuid as _uuid
    promo = (await db.execute(
        select(PromoCode).where(PromoCode.id == _uuid.UUID(promo_id))
    )).scalar_one_or_none()
    if not promo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promo code not found")
    promo.is_active = False
    await _audit(db, current_admin, "delete_promo", "promo", promo_id, {"code": promo.code})
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Billing: assign plan manually ─────────────────────────────────────────────

@router.post("/billing/assign", status_code=status.HTTP_200_OK)
async def admin_assign_plan(
    body: AssignPlanRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    plan = (await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == body.plan_slug)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")

    user = (await db.execute(
        select(User).where(User.id == body.user_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Cancel existing
    existing = (await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == body.user_id,
            UserSubscription.status == "active",
        )
    )).scalar_one_or_none()
    if existing:
        existing.status = "cancelled"

    sub = UserSubscription(
        user_id=body.user_id,
        plan_id=plan.id,
        billing_period=body.billing_period,
        status="active",
    )
    db.add(sub)
    await _audit(db, current_admin, "assign_plan", "user", str(body.user_id),
                 {"plan": body.plan_slug, "note": body.note})
    await db.commit()
    return {"ok": True, "plan": body.plan_slug}


# ── Segments admin ────────────────────────────────────────────────────────────

@router.get("/segments")
async def admin_list_segments(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: str | None = Query(None),
) -> list[dict]:
    q = select(SegmentUpload).order_by(SegmentUpload.created_at.desc()).offset(offset).limit(limit)
    if user_id:
        import uuid as _uuid
        q = q.where(SegmentUpload.user_id == _uuid.UUID(user_id))
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "campaign_id": str(s.campaign_id),
            "ad_platform": s.ad_platform,
            "status": s.status,
            "lookalike": s.lookalike,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in rows
    ]


@router.delete("/segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_segment(
    segment_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    import uuid as _uuid
    seg = (await db.execute(
        select(SegmentUpload).where(SegmentUpload.id == _uuid.UUID(segment_id))
    )).scalar_one_or_none()
    if not seg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Segment not found")
    await _audit(db, current_admin, "delete_segment", "segment", segment_id, {"user_id": str(seg.user_id)})
    await db.delete(seg)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_model=list[AdminAuditLogOut])
async def admin_audit_log(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
) -> list[AdminAuditLogOut]:
    q = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit)
    if action:
        q = q.where(AdminAuditLog.action == action)
    rows = (await db.execute(q)).scalars().all()
    return [AdminAuditLogOut.model_validate(r) for r in rows]


# ── Platform settings ─────────────────────────────────────────────────────────
#
#  Ключи:  wb_service_key  — WB сервисный секрет (JWT-токен авторизованного сервиса)
#
_ALLOWED_SETTING_KEYS = {"wb_service_key"}


@router.get("/settings/platform")
async def admin_get_platform_settings(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Возвращает мета-информацию о платформенных настройках (не сами секреты)."""
    from app.models.platform_settings import PlatformSetting
    from sqlalchemy import select as sa_select
    rows = (await db.execute(sa_select(PlatformSetting))).scalars().all()
    result: dict = {k: {"set": False, "updated_at": None, "updated_by": None}
                    for k in _ALLOWED_SETTING_KEYS}
    for row in rows:
        if row.key in result:
            result[row.key] = {
                "set": bool(row.value_enc),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "updated_by": row.updated_by,
            }
    return result


@router.put("/settings/platform/{key}")
async def admin_set_platform_setting(
    key: str,
    body: dict,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Сохраняет значение платформенной настройки (зашифровано)."""
    if key not in _ALLOWED_SETTING_KEYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Unknown setting key. Allowed: {sorted(_ALLOWED_SETTING_KEYS)}")
    value = body.get("value", "").strip()
    if not value:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="value is required")
    await set_platform_setting(key, value, current_admin.email, db)
    await _audit(db, current_admin, f"set_platform_setting", "platform_settings", key,
                 {"key": key})
    return {"ok": True, "key": key}


@router.delete("/settings/platform/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_platform_setting(
    key: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Удаляет платформенную настройку."""
    if key not in _ALLOWED_SETTING_KEYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Unknown setting key.")
    await delete_platform_setting(key, current_admin.email, db)
    await _audit(db, current_admin, "delete_platform_setting", "platform_settings", key,
                 {"key": key})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Internal helper ───────────────────────────────────────────────────────────

async def _audit(
    db: AsyncSession,
    admin: User,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict | None = None,
) -> None:
    log = AdminAuditLog(
        admin_id=admin.id,
        admin_email=admin.email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )
    db.add(log)
