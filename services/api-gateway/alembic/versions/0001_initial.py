"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── extensions ────────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.Text, nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── ad_platform_connections ───────────────────────────────────────────────
    op.create_table(
        "ad_platform_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("access_token_enc", sa.Text, nullable=False),
        sa.Column("refresh_token_enc", sa.Text),
        sa.Column("account_id", sa.Text),
        sa.Column("account_name", sa.Text),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "platform", "account_id", name="uq_ad_connections_user_platform_account"),
    )
    op.create_index("ix_ad_connections_user", "ad_platform_connections", ["user_id"])

    # ── marketplace_connections ───────────────────────────────────────────────
    op.create_table(
        "marketplace_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace", sa.String(32), nullable=False),
        sa.Column("api_key_enc", sa.Text, nullable=False),
        sa.Column("client_id", sa.Text),
        sa.Column("seller_id", sa.Text),
        sa.Column("marketplace_name", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "marketplace", "client_id", name="uq_mp_connections_user_marketplace_client"),
    )
    op.create_index("ix_mp_connections_user", "marketplace_connections", ["user_id"])

    # ── campaigns ─────────────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("marketplace", sa.String(32), nullable=False),
        sa.Column("ad_platform", sa.String(32), nullable=False),
        sa.Column("destination_url", sa.Text, nullable=False),
        sa.Column("budget", sa.Numeric(12, 2)),
        sa.Column("utm_source", sa.Text),
        sa.Column("utm_medium", sa.Text),
        sa.Column("utm_campaign", sa.Text),
        sa.Column("external_campaign_id", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_campaigns_user", "campaigns", ["user_id"])
    op.create_index("ix_campaigns_platform", "campaigns", ["ad_platform"])
    op.create_index("ix_campaigns_marketplace", "campaigns", ["marketplace"])

    # ── tracking_links ────────────────────────────────────────────────────────
    op.create_table(
        "tracking_links",
        sa.Column("trax_id", sa.Text, primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_url", sa.Text, nullable=False),
        sa.Column("utm_source", sa.Text),
        sa.Column("utm_medium", sa.Text),
        sa.Column("utm_campaign", sa.Text),
        sa.Column("utm_content", sa.Text),
        sa.Column("utm_term", sa.Text),
        sa.Column("label", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_tracking_links_campaign", "tracking_links", ["campaign_id"])

    # ── segment_uploads ───────────────────────────────────────────────────────
    op.create_table(
        "segment_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ad_platform", sa.String(32), nullable=False),
        sa.Column("lookalike", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("lookalike_scale", sa.Integer),
        sa.Column("min_roas_threshold", sa.Numeric(6, 2), nullable=False, server_default="3.0"),
        sa.Column("seed_size", sa.Integer),
        sa.Column("celery_task_id", sa.Text),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("external_segment_id", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_segments_user", "segment_uploads", ["user_id"])
    op.create_index("ix_segments_campaign", "segment_uploads", ["campaign_id"])
    op.create_index("ix_segments_status", "segment_uploads", ["status"])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("payload", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"])
    op.create_index("ix_notifications_created", "notifications", ["created_at"])

    # ── attribution_settings ──────────────────────────────────────────────────
    op.create_table(
        "attribution_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace", sa.String(32), nullable=False),
        sa.Column("window_days", sa.Integer, nullable=False, server_default="14"),
        sa.Column("method", sa.String(16), nullable=False, server_default="probabilistic"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "marketplace", name="uq_attribution_settings_user_marketplace"),
    )

    # ── updated_at trigger ────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    for table in ("users", "campaigns", "segment_uploads", "attribution_settings"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at()
        """)


def downgrade() -> None:
    for table in ("users", "campaigns", "segment_uploads", "attribution_settings"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at")

    op.drop_table("attribution_settings")
    op.drop_table("notifications")
    op.drop_table("segment_uploads")
    op.drop_table("tracking_links")
    op.drop_table("campaigns")
    op.drop_table("marketplace_connections")
    op.drop_table("ad_platform_connections")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
