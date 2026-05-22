"""
Public billing API.

GET  /billing/tariffs/public   — list active plans (no auth)
POST /billing/subscribe        — create subscription (auth required)
GET  /billing/usage            — current usage vs limits (auth required)
POST /billing/promo            — validate promo code (auth required)
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.billing import PromoCode, SubscriptionPlan, UserSubscription
from app.models.user import User
from app.schemas.billing import (
    PromoCheckRequest,
    PromoCheckResponse,
    PublicPlanOut,
    SubscribeRequest,
    SubscribeResponse,
    UsageLimitItem,
    UsageResponse,
)
from app.utils.deps import get_current_user

router = APIRouter()

_LIMIT_LABELS = {
    "clicks": "Отслеживаемых переходов / мес",
    "stores_wb": "Магазины WB / Ozon",
    "stores_ym": "Магазины Яндекс.Маркет",
    "ad_cabinets": "Рекламных кабинетов",
}


# ── Public: plan list ─────────────────────────────────────────────────────────

@router.get("/tariffs/public", response_model=list[PublicPlanOut])
async def public_tariffs(db: AsyncSession = Depends(get_db)) -> list[PublicPlanOut]:
    rows = (
        await db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.sort_order)
        )
    ).scalars().all()
    return [PublicPlanOut.model_validate(r) for r in rows]


# ── Subscribe ─────────────────────────────────────────────────────────────────

@router.post("/subscribe", response_model=SubscribeResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscribeResponse:
    # Resolve plan
    plan_row = (await db.execute(
        select(SubscriptionPlan).where(
            SubscriptionPlan.slug == body.plan_slug,
            SubscriptionPlan.is_active.is_(True),
        )
    )).scalar_one_or_none()
    if not plan_row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")

    # Validate promo
    promo_id = None
    if body.promo_code:
        promo = (await db.execute(
            select(PromoCode).where(
                PromoCode.code == body.promo_code.upper(),
                PromoCode.is_active.is_(True),
            )
        )).scalar_one_or_none()
        if not promo:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Promo code not found or inactive")
        if promo.valid_until and promo.valid_until < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Promo code has expired")
        if promo.max_uses and promo.used_count >= promo.max_uses:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Promo code usage limit reached")
        if promo.plan_slug and promo.plan_slug != body.plan_slug:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Promo code is not valid for this plan")
        promo_id = promo.id

    # Cancel existing active subscription
    existing = (await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active",
        )
    )).scalar_one_or_none()
    if existing:
        existing.status = "cancelled"

    # Create new subscription
    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan_row.id,
        billing_period=body.billing_period,
        promo_code_id=promo_id,
        status="active" if plan_row.slug == "free" else "pending_payment",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    # For paid plans, construct payment URL (placeholder — real integration with YooKassa/CloudPayments)
    payment_url = None
    if plan_row.slug != "free":
        # In production: create payment in YooKassa and return confirmation_url
        payment_url = f"https://pay.attribly.ru/checkout?sub={sub.id}&return={body.return_url or '/'}"

    return SubscribeResponse(
        subscription_id=sub.id,
        payment_url=payment_url,
        status=sub.status,
    )


# ── Usage ─────────────────────────────────────────────────────────────────────

@router.get("/usage", response_model=UsageResponse)
async def usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    # Get active subscription
    sub = (await db.execute(
        select(UserSubscription).where(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active",
        )
    )).scalar_one_or_none()

    if not sub:
        # Default to free plan limits
        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.slug == "free")
        )).scalar_one_or_none()
    else:
        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
        )).scalar_one_or_none()

    if not plan:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Plan configuration missing")

    # Build usage items (used values are 0 here — real impl queries ClickHouse)
    limit_items = [
        UsageLimitItem(
            key=k,
            label=_LIMIT_LABELS.get(k, k),
            used=0,
            limit=v,
        )
        for k, v in (plan.limits or {}).items()
    ]

    return UsageResponse(
        plan_slug=plan.slug,
        billing_period=sub.billing_period if sub else "monthly",
        status=sub.status if sub else "active",
        current_period_end=sub.current_period_end if sub else None,
        limits=limit_items,
    )


# ── Promo code check ──────────────────────────────────────────────────────────

@router.post("/promo", response_model=PromoCheckResponse)
async def check_promo(
    body: PromoCheckRequest,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromoCheckResponse:
    promo = (await db.execute(
        select(PromoCode).where(
            PromoCode.code == body.code.upper(),
            PromoCode.is_active.is_(True),
        )
    )).scalar_one_or_none()

    if not promo:
        return PromoCheckResponse(valid=False, message="Промокод не найден или недействителен.")
    if promo.valid_until and promo.valid_until < datetime.now(timezone.utc):
        return PromoCheckResponse(valid=False, message="Срок действия промокода истёк.")
    if promo.max_uses and promo.used_count >= promo.max_uses:
        return PromoCheckResponse(valid=False, message="Лимит использований промокода исчерпан.")
    if promo.plan_slug and promo.plan_slug != body.plan_slug:
        return PromoCheckResponse(valid=False, message=f"Промокод действует только для тарифа «{promo.plan_slug}».")

    discount_label = f"{round(promo.discount_pct * 100)}%"
    return PromoCheckResponse(
        valid=True,
        discount_pct=promo.discount_pct,
        message=f"Промокод применён — скидка {discount_label}.",
    )
