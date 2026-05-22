"""Billing tables (subscription_plans, user_subscriptions, promo_codes) and admin_audit_log

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── subscription_plans ────────────────────────────────────────────────────
    op.create_table(
        "subscription_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("price_monthly", sa.Float, nullable=False, server_default="0"),
        sa.Column("price_yearly", sa.Float, nullable=False, server_default="0"),
        sa.Column("limits", JSONB, nullable=False, server_default="{}"),
        sa.Column("features", JSONB, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_plans_slug", "subscription_plans", ["slug"])
    op.create_index("ix_plans_active", "subscription_plans", ["is_active"])

    # ── user_subscriptions ────────────────────────────────────────────────────
    op.create_table(
        "user_subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), nullable=False),
        sa.Column("billing_period", sa.String(8), nullable=False, server_default="monthly"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("promo_code_id", UUID(as_uuid=True), nullable=True),
        sa.Column("external_subscription_id", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_user", "user_subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "user_subscriptions", ["status"])

    # ── promo_codes ───────────────────────────────────────────────────────────
    op.create_table(
        "promo_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("discount_pct", sa.Float, nullable=False),
        sa.Column("max_uses", sa.Integer, nullable=True),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("plan_slug", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_promo_code", "promo_codes", ["code"])

    # ── admin_audit_log ───────────────────────────────────────────────────────
    op.create_table(
        "admin_audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_id", UUID(as_uuid=True), nullable=False),
        sa.Column("admin_email", sa.Text, nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=True),
        sa.Column("target_id", sa.Text, nullable=True),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_admin", "admin_audit_log", ["admin_id"])
    op.create_index("ix_audit_action", "admin_audit_log", ["action"])
    op.create_index("ix_audit_created", "admin_audit_log", ["created_at"])

    # Seed default plans via bulk_insert to avoid SQLAlchemy colon-param parsing issues
    import json, uuid as _uuid
    plans_table = sa.table(
        "subscription_plans",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("price_monthly", sa.Float),
        sa.column("price_yearly", sa.Float),
        sa.column("limits", JSONB),
        sa.column("features", JSONB),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(plans_table, [
        dict(id=_uuid.uuid4(), slug="free",       name="Free",       price_monthly=0,      price_yearly=0,
             limits={"clicks": 500,   "stores_wb": 1,  "stores_ym": 1, "ad_cabinets": 1},
             features=["Базовая аналитика", "1 магазин WB/Ozon"], is_active=True, sort_order=0),
        dict(id=_uuid.uuid4(), slug="start",      name="Start",      price_monthly=7190,   price_yearly=68000,
             limits={"clicks": 5000,  "stores_wb": 2,  "stores_ym": 1, "ad_cabinets": 3},
             features=["Базовая атрибуция WB", "3 рекламных кабинета"], is_active=True, sort_order=1),
        dict(id=_uuid.uuid4(), slug="business",   name="Business",   price_monthly=19190,  price_yearly=184000,
             limits={"clicks": 50000, "stores_wb": 10, "stores_ym": 3, "ad_cabinets": -1},
             features=["ML-атрибуция", "Look-alike аудитории", "Logistics Tracker", "ИИ-ассистент 50/мес"],
             is_active=True, sort_order=2),
        dict(id=_uuid.uuid4(), slug="enterprise", name="Enterprise", price_monthly=47990,  price_yearly=459000,
             limits={"clicks": -1,    "stores_wb": -1, "stores_ym": -1, "ad_cabinets": -1},
             features=["ML-атрибуция + ручная верификация", "Look-alike + автоактивация", "ИИ-ассистент без ограничений"],
             is_active=True, sort_order=3),
    ])


def downgrade() -> None:
    op.drop_table("admin_audit_log")
    op.drop_table("promo_codes")
    op.drop_table("user_subscriptions")
    op.drop_table("subscription_plans")
