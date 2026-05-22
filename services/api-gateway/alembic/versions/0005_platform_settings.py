"""Platform settings table for admin-managed secrets (e.g. WB service key)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value_enc", sa.Text, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
