from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

IntegrationType = Literal["marketplace", "ad_platform"]

MarketplaceProvider = Literal["ozon", "wildberries", "yandex_market", "amazon"]
AdProvider = Literal[
    "yandex_direct", "vk_ads", "vk_blogger", "telegram_ads", "messenger_max"
]


# ── Request bodies ─────────────────────────────────────────────────────────────

class MarketplaceConnectRequest(BaseModel):
    provider: MarketplaceProvider
    api_key: str
    client_id: str | None = None
    seller_id: str | None = None


class AdConnectRequest(BaseModel):
    provider: AdProvider
    access_token: str
    refresh_token: str | None = None
    account_id: str | None = None
    account_name: str | None = None


# ── Response ───────────────────────────────────────────────────────────────────

class IntegrationResponse(BaseModel):
    """Unified view of marketplace_connections and ad_platform_connections."""
    model_config = {"from_attributes": True}

    id: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v): return str(v)
    type: IntegrationType
    provider: str
    account_name: str | None
    status: str                        # pending | active | error
    last_synced_at: datetime | None
    created_at: datetime


class ValidateResponse(BaseModel):
    ok: bool
    message: str
