"""
Performance router - unified analytics across ad platforms
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter()


class PerformanceMetrics(BaseModel):
    impressions: int
    clicks: int
    spent: float
    conversions: int
    revenue: float
    ctr: float
    cpc: float
    roas: float


class CampaignPerformance(BaseModel):
    provider: str
    campaign_id: str
    campaign_name: str
    date: date
    metrics: PerformanceMetrics


@router.get("/performance")
async def get_unified_performance(
    date_from: date,
    date_to: date,
    provider: Optional[str] = None,
) -> dict:
    """
    Get unified performance metrics across all connected ad platforms
    
    Aggregates data from:
    - Yandex Direct
    - VK Ads
    - Telegram Ads
    - VK Blogger
    """
    # TODO: Implement unified performance aggregation
    pass


@router.get("/performance/by-campaign")
async def get_performance_by_campaign(
    date_from: date,
    date_to: date,
    provider: Optional[str] = None,
) -> list[CampaignPerformance]:
    """
    Get performance metrics broken down by campaign
    """
    # TODO: Implement campaign-level performance
    pass
