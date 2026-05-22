"""
Attribly Canvas models: CanvasBoard, BoardWidget, BoardConnection, BoardTemplate.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.postgres import Base


class CanvasBoard(Base):
    __tablename__ = "canvas_boards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Новый канвас")
    description: Mapped[str | None] = mapped_column(Text)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    # Sharing
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    # Viewport state (last position user left at)
    viewport_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    viewport_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    viewport_zoom: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoardWidget(Base):
    __tablename__ = "board_widgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canvas_boards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Type: product_card | logistics | ad_connector | mini_chart | sticker | text | kpi_table
    widget_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Position (world coordinates)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[float] = mapped_column(Float, nullable=False, default=300.0)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=200.0)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Widget-specific config: store_id, external_product_id, campaign_id, content, color, …
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Visual overrides: locked, bg_color, border_color, …
    style: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoardConnection(Base):
    __tablename__ = "board_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canvas_boards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_widget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("board_widgets.id", ondelete="CASCADE"), nullable=False
    )
    to_widget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("board_widgets.id", ondelete="CASCADE"), nullable=False
    )
    # style: {type: solid|dashed, color: #B0C4DE, thickness: 2}
    style: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    label: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoardTemplate(Base):
    __tablename__ = "board_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # pnl_sku | brand_rollout | traffic_analysis | logistics | competitor | blank
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    thumbnail_emoji: Mapped[str] = mapped_column(String(8), nullable=False, default="📋")
    # JSON: {widgets: [{type, x, y, w, h, data, style}], connections: [...]}
    template_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
