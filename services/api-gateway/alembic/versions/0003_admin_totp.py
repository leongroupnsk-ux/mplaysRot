"""Admin role and TOTP secret column

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("totp_secret", sa.Text, nullable=True),
    )
    # Widen role column to accommodate "admin" (still fits in 16 chars)
    # No structural change needed — "admin" is 5 chars, column is String(16)


def downgrade() -> None:
    op.drop_column("users", "totp_secret")
