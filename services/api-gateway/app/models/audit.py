"""Immutable admin audit log."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class AdminAuditLog(Base):
    """Append-only log of all admin actions. Never updated or deleted."""
    __tablename__ = "admin_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    admin_email: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # e.g. "create_plan", "update_plan", "delete_plan", "assign_plan", "create_promo",
    #      "delete_promo", "view_sensitive", "block_user", "change_role"
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "plan"|"user"|"promo"|"segment"
    target_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)          # diff / relevant data snapshot
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
