from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── Public tariff ─────────────────────────────────────────────────────────────

class PublicPlanOut(BaseModel):
    id: UUID
    slug: str
    name: str
    price_monthly: float
    price_yearly: float
    limits: dict[str, Any]
    features: list[str]
    sort_order: int

    model_config = {"from_attributes": True}


# ── Subscription ──────────────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    plan_slug: str
    billing_period: str = Field("monthly", pattern="^(monthly|yearly)$")
    promo_code: Optional[str] = None
    return_url: Optional[str] = None          # redirect after payment


class SubscribeResponse(BaseModel):
    subscription_id: UUID
    payment_url: Optional[str] = None         # redirect to YooKassa / CloudPayments
    status: str                               # "pending_payment" | "active" (for free plan)


class UsageLimitItem(BaseModel):
    key: str
    label: str
    used: int
    limit: int                                # -1 = unlimited


class UsageResponse(BaseModel):
    plan_slug: str
    billing_period: str
    status: str
    current_period_end: Optional[datetime]
    limits: list[UsageLimitItem]


# ── Promo code ────────────────────────────────────────────────────────────────

class PromoCheckRequest(BaseModel):
    code: str
    plan_slug: str


class PromoCheckResponse(BaseModel):
    valid: bool
    discount_pct: float = 0.0
    message: str


# ── Admin billing schemas ──────────────────────────────────────────────────────

class PlanCreateRequest(BaseModel):
    slug: str
    name: str
    price_monthly: float
    price_yearly: float
    limits: dict[str, Any] = {}
    features: list[str] = []
    sort_order: int = 0


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    limits: Optional[dict[str, Any]] = None
    features: Optional[list[str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class AdminPlanOut(PublicPlanOut):
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromoCreateRequest(BaseModel):
    code: str
    discount_pct: float = Field(..., gt=0, le=1)
    max_uses: Optional[int] = None
    valid_until: Optional[datetime] = None
    plan_slug: Optional[str] = None


class AdminPromoOut(BaseModel):
    id: UUID
    code: str
    discount_pct: float
    max_uses: Optional[int]
    used_count: int
    valid_until: Optional[datetime]
    plan_slug: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignPlanRequest(BaseModel):
    user_id: UUID
    plan_slug: str
    billing_period: str = "monthly"
    note: Optional[str] = None   # stored in audit payload


class AdminAuditLogOut(BaseModel):
    id: UUID
    admin_email: str
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    payload: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
