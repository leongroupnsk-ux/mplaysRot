from __future__ import annotations
from pydantic import BaseModel
from datetime import date
from typing import Optional


class PeriodMetrics(BaseModel):
    total_spend: float
    total_revenue: float
    roas: float
    attributed_orders: int
    click_to_order_rate: float
    avg_order_value: float


class OverviewResponse(PeriodMetrics):
    date_from: date
    date_to: date
    previous_period: Optional[PeriodMetrics] = None


class FunnelStep(BaseModel):
    name: str
    count: int
    conversion_rate: float


class FunnelResponse(BaseModel):
    campaign_id: str
    steps: list[FunnelStep]


class GeoResponse(BaseModel):
    region: str
    clicks: int
    orders: int
    revenue: float
    conversion_rate: float


class TimeSeriesPoint(BaseModel):
    date: str
    spend: float
    revenue: float
    clicks: int
    orders: int
    roas: float


class TopCreativeRow(BaseModel):
    external_ad_id: str
    ad_name: str
    ad_platform: str
    spend: float
    clicks: int
    orders: int
    roas: float


class ClickToOrderBucket(BaseModel):
    bucket_label: str
    count: int
    pct: float
