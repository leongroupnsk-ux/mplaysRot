from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator


class NotificationResponse(BaseModel):
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v): return str(v)
    campaign_id: str | None
    type: str
    title: str
    body: str
    is_read: bool
    payload: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
