"""Stores and products catalog

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── status column on existing connection tables ────────────────────────────
    op.add_column(
        "marketplace_connections",
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
    )
    op.add_column(
        "ad_platform_connections",
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
    )

    # ── stores ────────────────────────────────────────────────────────────────
    # Populated automatically after a marketplace connection is validated.
    op.create_table(
        "stores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "marketplace_connection_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketplace_connections.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_store_id", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("logo_url", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_stores_user", "stores", ["user_id"])
    op.create_index("ix_stores_provider", "stores", ["provider"])

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "store_id",
            UUID(as_uuid=True),
            sa.ForeignKey("stores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        # External identifier — nmID for WB, offer_id for Ozon, offerId for YM, ASIN for Amazon
        sa.Column("external_product_id", sa.Text, nullable=False),
        # parent_external_id is NULL for root products, filled for variation children
        sa.Column("parent_external_id", sa.Text),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("stock", sa.Integer, nullable=False, server_default="0"),
        sa.Column("image_url", sa.Text),
        sa.Column("has_variations", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_orphaned", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "store_id", "external_product_id",
            name="uq_products_store_external_id",
        ),
    )
    op.create_index("ix_products_user", "products", ["user_id"])
    op.create_index("ix_products_store", "products", ["store_id"])
    op.create_index("ix_products_external_id", "products", ["external_product_id"])
    op.create_index("ix_products_parent", "products", ["parent_external_id"])
    op.create_index("ix_products_active", "products", ["store_id", "is_active", "is_archived"])

    # ── updated_at triggers ───────────────────────────────────────────────────
    for table in ("stores", "products"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at()
        """)


def downgrade() -> None:
    for table in ("stores", "products"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.drop_table("products")
    op.drop_table("stores")

    op.drop_column("ad_platform_connections", "status")
    op.drop_column("marketplace_connections", "status")
