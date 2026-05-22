"""Billing models: subscription plans, user subscriptions, promo codes."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class SubscriptionPlan(Base):
    """Defines a publicly available tariff tier."""
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)   # free|start|business|enterprise
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    price_yearly: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    limits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)    # {"clicks":500,"stores_wb":1,...}
    features: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # list of feature strings
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserSubscription(Base):
    """Active subscription for a user."""
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    billing_period: Mapped[str] = mapped_column(String(8), nullable=False, default="monthly")  # monthly|yearly
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")          # active|frozen|cancelled
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    promo_code_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    external_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)  # YooKassa / CloudPayments id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromoCode(Base):
    """Promotional discount codes."""
    __tablename__ = "promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=False)      # 0.0–1.0
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_slug: Mapped[str | None] = mapped_column(String(32), nullable=True)  # restrict to specific plan, or null = any
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
