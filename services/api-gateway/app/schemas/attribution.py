from pydantic import BaseModel
from datetime import datetime


class AttributionLogEntry(BaseModel):
    order_id: str
    campaign_id: str
    trax_id: str
    marketplace: str
    ad_platform: str
    product_id: str
    order_amount: float
    click_at: datetime
    order_at: datetime
    time_to_order_hours: float
    confidence: float
    attribution_method: str
