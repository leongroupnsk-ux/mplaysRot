"""
Integrations router - OAuth flow and connection management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class IntegrationAuthRequest(BaseModel):
    provider: str  # yandex_direct, vk_ads, telegram_ads, vk_blogger
    redirect_uri: str


class IntegrationStatus(BaseModel):
    provider: str
    is_connected: bool
    user_id: int
    last_sync: Optional[str]
    token_expires_at: Optional[str]


@router.post("/{provider}/auth")
async def start_oauth_flow(provider: str, request: IntegrationAuthRequest):
    """
    Initiate OAuth flow for a specific provider
    
    Supported providers:
    - yandex_direct
    - vk_ads
    - telegram_ads
    - vk_blogger
    """
    # TODO: Implement OAuth flow initiation
    # Should return authorization URL
    pass


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str):
    """
    OAuth callback handler - exchanges code for token
    """
    # TODO: Implement token exchange
    pass


@router.get("/{provider}/status")
async def get_integration_status(provider: str) -> IntegrationStatus:
    """
    Get connection status for a specific provider
    """
    # TODO: Implement status check
    pass


@router.delete("/{provider}/disconnect")
async def disconnect_integration(provider: str):
    """
    Disconnect and revoke access to a provider
    """
    # TODO: Implement disconnection
    pass


@router.post("/{provider}/sync")
async def manual_sync(provider: str):
    """
    Trigger manual sync for a provider (statistics, audiences, etc.)
    """
    # TODO: Implement manual sync
    pass
