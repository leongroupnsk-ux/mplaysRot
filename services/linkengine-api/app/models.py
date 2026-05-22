from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ───────────────────────────────────────────────────────────────────────
# Enums
# ───────────────────────────────────────────────────────────────────────

class MarketplaceType(str, Enum):
    """Supported marketplace types"""
    WB = "wildberries"
    OZON = "ozon"


class LinkType(str, Enum):
    """Types of links that can be generated"""
    DEEPLINK = "deeplink"
    MULTILINK = "multilink"
    AUTOLANDING = "autolanding"


class CustomDomainStatus(str, Enum):
    """Status of custom domain"""
    PENDING_PAYMENT = "pending_payment"
    PENDING_CNAME = "pending_cname"
    PENDING_SSL = "pending_ssl"
    ACTIVE = "active"
    SSL_ERROR = "ssl_error"
    SUSPENDED = "suspended"


# ───────────────────────────────────────────────────────────────────────
# Request Models
# ───────────────────────────────────────────────────────────────────────

class UTMMetadata(BaseModel):
    """UTM parameters for tracking"""
    utm_source: str = Field(..., description="Traffic source (e.g., yandex_ads, vk)")
    utm_medium: str = Field(..., description="Traffic medium (e.g., cpc, social)")
    utm_campaign: str = Field(..., description="Campaign name/ID")
    utm_term: Optional[str] = Field(None, description="Keyword/term")
    utm_content: Optional[str] = Field(None, description="Ad variant/content")


class GenerateDiplinkRequest(BaseModel):
    """Request to generate a deeplink"""
    store_id: int
    marketplace: MarketplaceType
    external_product_id: str = Field(..., description="SKU/Article from marketplace")
    utm_metadata: UTMMetadata
    custom_domain_id: Optional[int] = Field(None, description="ID of custom domain to use")
    title: Optional[str] = Field(None, description="Link title for tracking")


class GenerateDiplinkResponse(BaseModel):
    """Response for deeplink generation (same as DiplinkResponse)"""
    pass


class GenerateMultilinkRequest(BaseModel):
    """Request to generate multilink (multiple marketplace links)"""
    store_id: int
    products: List[Dict[str, Any]] = Field(
        ...,
        description="List of {marketplace, external_product_id}",
        example=[
            {"marketplace": "wildberries", "external_product_id": "123456"},
            {"marketplace": "ozon", "external_product_id": "654321"},
        ]
    )
    utm_metadata: UTMMetadata
    custom_domain_id: Optional[int] = Field(None)
    title: Optional[str] = None


class GenerateAutolendingRequest(BaseModel):
    """Request to generate auto-landing"""
    store_id: int
    marketplace: MarketplaceType
    external_product_id: str
    template_id: Optional[int] = Field(1, description="Landing template ID (1-3)")
    custom_domain_id: Optional[int] = None
    title: Optional[str] = None


class VerifyProductRequest(BaseModel):
    """Request to verify product belongs to store"""
    store_id: int
    external_product_id: str
    marketplace: MarketplaceType


# ───────────────────────────────────────────────────────────────────────
# Response Models
# ───────────────────────────────────────────────────────────────────────

class DiplinkResponse(BaseModel):
    """Generated deeplink response"""
    id: str = Field(..., description="Unique link ID")
    short_code: str = Field(..., description="Short code for redirection")
    short_url: str = Field(..., description="Short URL (e.g., https://attribly.ru/l/abc123)")
    full_deeplink: str = Field(..., description="Full deeplink with UTM parameters")
    qr_code_url: Optional[str] = Field(None, description="QR code as data URL")
    marketplace: MarketplaceType
    external_product_id: str
    utm_metadata: UTMMetadata
    created_at: datetime
    expires_at: Optional[datetime] = None


class MultiLinkResponse(BaseModel):
    """Generated multilink response"""
    id: str
    short_code: str
    short_url: str
    landing_url: str = Field(..., description="URL to auto-landing with multiple CTA buttons")
    links: List[DiplinkResponse] = Field(..., description="List of deeplinks in multilink")
    created_at: datetime


class AutolandingResponse(BaseModel):
    """Generated auto-landing response"""
    id: str
    landing_url: str = Field(..., description="URL to rendered landing page")
    product_title: str
    marketplace: MarketplaceType
    external_product_id: str
    template_id: int
    created_at: datetime


class VerifyProductResponse(BaseModel):
    """Product verification response"""
    verified: bool
    external_product_id: str
    store_id: int
    marketplace: MarketplaceType
    product_title: Optional[str] = None
    is_active: bool = Field(True, description="Whether product is active in store")
    reason: Optional[str] = Field(None, description="Reason if verification failed")


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
