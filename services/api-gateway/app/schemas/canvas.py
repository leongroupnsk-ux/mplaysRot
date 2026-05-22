from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator
import uuid


# ── Boards ────────────────────────────────────────────────────────────────────

class BoardCreate(BaseModel):
    title: str = "Новый канвас"
    description: Optional[str] = None
    template_id: Optional[str] = None


class BoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    viewport_x: Optional[float] = None
    viewport_y: Optional[float] = None
    viewport_zoom: Optional[float] = None
    is_public: Optional[bool] = None


class BoardOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    is_public: bool
    share_token: Optional[str] = None
    viewport_x: float
    viewport_y: float
    viewport_zoom: float
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)

    @field_validator("template_id", mode="before")
    @classmethod
    def coerce_uuid_opt(cls, v):
        return str(v) if v else None


# ── Widgets ───────────────────────────────────────────────────────────────────

class WidgetCreate(BaseModel):
    widget_type: str
    x: float = 100.0
    y: float = 100.0
    width: float = 300.0
    height: float = 200.0
    z_index: int = 0
    data: dict[str, Any] = {}
    style: dict[str, Any] = {}


class WidgetUpdate(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    z_index: Optional[int] = None
    data: Optional[dict[str, Any]] = None
    style: Optional[dict[str, Any]] = None


class WidgetBulkUpdate(BaseModel):
    """Batch update widget positions (e.g. after multi-drag)."""
    updates: list[dict[str, Any]]  # [{id, x, y, z_index?}]


class WidgetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    board_id: str
    widget_type: str
    x: float
    y: float
    width: float
    height: float
    z_index: int
    data: dict[str, Any]
    style: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "board_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)


# ── Connections ───────────────────────────────────────────────────────────────

class ConnectionCreate(BaseModel):
    from_widget_id: str
    to_widget_id: str
    style: dict[str, Any] = {}
    label: Optional[str] = None


class ConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    board_id: str
    from_widget_id: str
    to_widget_id: str
    style: dict[str, Any]
    label: Optional[str] = None
    created_at: datetime

    @field_validator("id", "board_id", "from_widget_id", "to_widget_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)


# ── Full board detail ─────────────────────────────────────────────────────────

class BoardDetailOut(BoardOut):
    widgets: list[WidgetOut] = []
    connections: list[ConnectionOut] = []


# ── Templates ─────────────────────────────────────────────────────────────────

class TemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: Optional[str] = None
    category: str
    thumbnail_emoji: str
    template_data: dict[str, Any]
    is_system: bool

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)


# ── Widget live data ──────────────────────────────────────────────────────────

class ProductWidgetData(BaseModel):
    external_product_id: str
    title: str
    image_url: Optional[str] = None
    price: Optional[str] = None
    stock: int = 0
    store_name: Optional[str] = None
    marketplace: Optional[str] = None


class LogisticsWidgetData(BaseModel):
    external_product_id: str
    title: str
    image_url: Optional[str] = None
    stock: int
    # Days of supply (rough estimate: stock / avg_daily_sales; placeholder)
    days_supply: Optional[int] = None
    status: str  # ok | warn | critical


class CampaignWidgetData(BaseModel):
    campaign_id: str
    name: str
    marketplace: str
    ad_platform: str
    is_active: bool
    budget: Optional[str] = None
    utm_source: Optional[str] = None


# ── AI command ────────────────────────────────────────────────────────────────

class AICommandRequest(BaseModel):
    command: str


class AICommandResponse(BaseModel):
    message: str
    actions: list[dict[str, Any]] = []
