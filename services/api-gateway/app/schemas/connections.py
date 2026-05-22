from pydantic import BaseModel
from datetime import datetime


class AdConnectionCreate(BaseModel):
    platform: str
    access_token: str
    refresh_token: str | None = None
    account_id: str | None = None


class AdConnectionResponse(BaseModel):
    id: str
    platform: str
    account_id: str | None
    account_name: str | None
    is_active: bool
    last_synced_at: datetime | None


class MarketplaceConnectionCreate(BaseModel):
    marketplace: str
    api_key: str
    service_key: str | None = None   # WB сервисный секрет
    client_id: str | None = None


class MarketplaceConnectionUpdate(BaseModel):
    service_key: str | None = None
    api_key: str | None = None


class MarketplaceConnectionResponse(BaseModel):
    id: str
    marketplace: str
    client_id: str | None
    marketplace_name: str | None
    is_active: bool
    last_synced_at: datetime | None
    has_service_key: bool = False
