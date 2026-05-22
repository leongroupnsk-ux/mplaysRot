from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class StoreResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    connection_id: str

    @field_validator("id", "connection_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v): return str(v)
    provider: str
    external_store_id: str
    name: str
    logo_url: str | None
    is_active: bool
    last_sync_at: datetime | None
    created_at: datetime


class ProductVariation(BaseModel):
    """Lightweight child SKU info shown in the '+N variants' tooltip."""
    external_product_id: str
    title: str
    stock: int


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    store_id: str

    @field_validator("id", "store_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v): return str(v)
    provider: str
    external_product_id: str
    parent_external_id: str | None
    title: str
    price: Decimal
    stock: int
    image_url: str | None
    has_variations: bool
    is_active: bool
    is_archived: bool
    # Populated only when has_variations=True and query includes expand_variations
    variations: list[ProductVariation] = []


class ProductSearchResponse(BaseModel):
    items: list[ProductResponse]
    total: int
