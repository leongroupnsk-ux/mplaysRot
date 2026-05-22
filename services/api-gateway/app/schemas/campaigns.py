from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from enum import Enum


class AdPlatform(str, Enum):
    yandex_direct = "yandex_direct"
    vk_ads = "vk_ads"
    vk_blogger = "vk_blogger"
    telegram_ads = "telegram_ads"
    messenger_max = "messenger_max"


class Marketplace(str, Enum):
    ozon = "ozon"
    wildberries = "wildberries"
    yandex_market = "yandex_market"
    amazon = "amazon"


class CampaignCreate(BaseModel):
    name: str
    marketplace: Marketplace
    ad_platform: AdPlatform
    destination_url: HttpUrl
    budget: float | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    budget: float | None = None
    is_active: bool | None = None


class CampaignResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v): return str(v)
    name: str
    marketplace: Marketplace
    ad_platform: AdPlatform
    destination_url: str
    budget: float | None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class TrackingLinkCreate(BaseModel):
    label: str | None = None
    destination_url: HttpUrl | None = None
    utm_content: str | None = None
    utm_term: str | None = None


class TrackingLinkResponse(BaseModel):
    model_config = {"from_attributes": True}

    trax_id: str
    tracking_url: str
    destination_url: str
    label: str | None
    created_at: datetime
