from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
import uuid


# ── DeepLink ──────────────────────────────────────────────────────────────────

class DeepLinkCreate(BaseModel):
    store_id: str
    marketplace: str
    external_product_id: str
    product_title: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[str] = None
    link_type: str = "deeplink"
    name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    custom_domain_id: Optional[str] = None


class DeepLinkUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class DeepLinkOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    store_id: str
    marketplace: str
    external_product_id: str
    product_title: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[str] = None
    link_type: str
    short_code: str
    name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    custom_domain_id: Optional[str] = None
    status: str
    click_count: int
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "user_id", "store_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)

    @field_validator("custom_domain_id", mode="before")
    @classmethod
    def coerce_uuid_opt(cls, v):
        return str(v) if v else None


class DeepLinkPublicOut(BaseModel):
    """Returned for public redirect page — no sensitive info."""
    id: str
    marketplace: str
    external_product_id: str
    product_title: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[str] = None
    link_type: str
    short_code: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    status: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)


class ClickTrackRequest(BaseModel):
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    device_type: Optional[str] = None  # mobile | desktop | tablet


class VerifySkuResponse(BaseModel):
    valid: bool
    product_title: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[str] = None
    message: Optional[str] = None


# ── CustomDomain ──────────────────────────────────────────────────────────────

class CustomDomainCreate(BaseModel):
    domain: str
    domain_type: str = "own"  # own | purchased


class CustomDomainOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    domain: str
    domain_type: str
    status: str
    cname_verified: bool
    ssl_type: Optional[str] = None
    ssl_expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)


class AdminDomainOut(CustomDomainOut):
    """Extended for admin view — includes user email."""
    user_email: Optional[str] = None
