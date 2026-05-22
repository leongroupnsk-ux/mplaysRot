"""
LinkEngine models: DeepLink, CustomDomain, LinkClick.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer,
    String, Text, UUID, func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.postgres import Base


class DeepLink(Base):
    __tablename__ = "deep_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Product info (denormalised for resilience)
    marketplace: Mapped[str] = mapped_column(String(32), nullable=False)  # wildberries | ozon
    external_product_id: Mapped[str] = mapped_column(Text, nullable=False)  # nm_id / product_id
    product_title: Mapped[str | None] = mapped_column(Text)
    product_image: Mapped[str | None] = mapped_column(Text)
    product_price: Mapped[str | None] = mapped_column(String(32))
    # Link config
    link_type: Mapped[str] = mapped_column(String(16), nullable=False, default="deeplink")  # deeplink | autolanding
    short_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    # UTM params
    utm_source: Mapped[str | None] = mapped_column(Text)
    utm_medium: Mapped[str | None] = mapped_column(Text)
    utm_campaign: Mapped[str | None] = mapped_column(Text)
    utm_term: Mapped[str | None] = mapped_column(Text)
    utm_content: Mapped[str | None] = mapped_column(Text)
    # Custom domain
    custom_domain_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    # State
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")  # active | paused | product_unavailable
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Name (optional, for display)
    name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LinkClick(Base):
    __tablename__ = "link_clicks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    deep_link_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deep_links.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[str | None] = mapped_column(String(16))  # mobile | desktop | tablet
    referer: Mapped[str | None] = mapped_column(Text)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(253), unique=True, nullable=False)
    domain_type: Mapped[str] = mapped_column(String(16), nullable=False, default="own")  # own | purchased
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_cname")
    # pending_cname | pending_ssl | active | error | suspended
    cname_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ssl_type: Mapped[str | None] = mapped_column(String(32))  # letsencrypt | sectigo
    ssl_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
