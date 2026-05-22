from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class SegmentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    uploaded = "uploaded"
    failed = "failed"


class SegmentUploadRequest(BaseModel):
    campaign_id: str
    ad_platform: str
    min_roas_threshold: float = 3.0
    lookalike: bool = False
    lookalike_scale: int = 5


class SegmentUploadResponse(BaseModel):
    task_id: str
    campaign_id: str
    ad_platform: str
    lookalike: bool = False
    seed_size: int | None
    status: SegmentStatus
    external_segment_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
