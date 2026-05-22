from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base for models
Base = declarative_base()


# ───────────────────────────────────────────────────────────────────────
# Database Models
# ───────────────────────────────────────────────────────────────────────

class StoreProduct(Base):
    """Store product mapping for SKU verification"""
    __tablename__ = "store_products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    external_product_id = Column(String(255), nullable=False)
    marketplace = Column(String(32), nullable=False)  # 'wildberries', 'ozon'
    title = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    synced_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("store_id", "external_product_id", "marketplace", name="uq_store_product_sku"),
        Index("ix_store_products_store_id_active", "store_id", "is_active"),
    )


class GeneratedLink(Base):
    """Record of all generated deeplinks"""
    __tablename__ = "generated_links"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    short_code = Column(String(10), unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    marketplace = Column(String(32), nullable=False)
    external_product_id = Column(String(255), nullable=False)
    link_type = Column(String(32), nullable=False)  # 'deeplink', 'multilink', 'autolanding'
    
    # Domain info
    custom_domain_id = Column(Integer, nullable=True)
    domain_name = Column(String(255), nullable=False)  # e.g., 'attribly.ru' or 'mybrand.ru'
    
    # UTM parameters
    utm_source = Column(String(255))
    utm_medium = Column(String(255))
    utm_campaign = Column(String(255))
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    
    # Tracking
    title = Column(String(500), nullable=True)
    click_count = Column(Integer, default=0)
    redirect_count = Column(Integer, default=0)
    
    # Deeplink payload
    full_deeplink = Column(Text, nullable=True)
    
    # QR code
    qr_code_data = Column(Text, nullable=True)  # Base64 encoded

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_generated_links_user_store", "user_id", "store_id"),
        Index("ix_generated_links_created_at", "created_at"),
    )


class LinkRedirectLog(Base):
    """Log of all redirects via generated links (for analytics)"""
    __tablename__ = "link_redirect_logs"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(String(36), ForeignKey("generated_links.id"), index=True)
    short_code = Column(String(10), index=True)
    
    # Request info
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv4/IPv6
    referer = Column(String(2048), nullable=True)
    
    # Device/OS detection
    device_type = Column(String(32))  # 'mobile', 'desktop', 'tablet'
    os = Column(String(64), nullable=True)  # 'ios', 'android', 'windows', etc.
    
    # Geo
    country = Column(String(2), nullable=True)  # ISO country code
    city = Column(String(100), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_redirect_logs_link_id_timestamp", "link_id", "timestamp"),
        Index("ix_redirect_logs_short_code_timestamp", "short_code", "timestamp"),
    )


class VerificationFailLog(Base):
    """Log of failed product verifications (fraud prevention)"""
    __tablename__ = "verification_fail_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    external_product_id = Column(String(255), nullable=False)
    marketplace = Column(String(32), nullable=False)
    
    reason = Column(String(255))  # 'not_found', 'inactive', 'deleted'
    ip_address = Column(String(45))
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_verification_fail_user_store", "user_id", "store_id"),
    )


class CustomDomain(Base):
    """Custom domain configuration"""
    __tablename__ = "custom_domains"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    domain_name = Column(String(255), unique=True, index=True)
    
    status = Column(String(32), default="pending_cname")  # Enum: pending_cname, active, suspended, etc.
    
    ssl_certificate_id = Column(String(255), nullable=True)
    ssl_provider = Column(String(64), nullable=True)  # 'letsencrypt', 'sectigo'
    ssl_expires_at = Column(DateTime, nullable=True)
    
    is_purchased = Column(Boolean, default=False)  # True if bought through Attribly
    purchased_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Domain expiration date
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LandingTemplate(Base):
    """Customized landing page templates"""
    __tablename__ = "landing_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    sku = Column(String(255), nullable=False)
    marketplace = Column(String(32), nullable=False)
    
    # Template base (1-3)
    template_id = Column(Integer, default=1)
    
    # Customizations (JSON would be better, but keeping as columns for now)
    hero_image_url = Column(String(2048), nullable=True)
    description = Column(Text, nullable=True)
    cta_button_color = Column(String(7), nullable=True)  # Hex color
    logo_url = Column(String(2048), nullable=True)
    show_reviews = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_landing_templates_user_sku", "user_id", "sku", "marketplace"),
    )


async def get_session():
    """Dependency for getting DB session"""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization warning: {e}")
        # Continue if tables already exist


async def close_db():
    """Close database connections"""
    await engine.dispose()
