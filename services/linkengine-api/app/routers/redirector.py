from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session, GeneratedLink, LinkRedirectLog
from app.models import DiplinkResponse
from app.device_detector import DeviceDetector
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["redirector"])


@router.get(
    "/l/{short_code}",
    response_class=RedirectResponse,
    summary="Redirect short link",
    description="Resolve a short code and redirect to the full deeplink",
)
async def redirect_short_link(
    short_code: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle redirect requests for short codes."""

    stmt = select(GeneratedLink).where(
        GeneratedLink.short_code == short_code,
        GeneratedLink.is_active == True,
    )
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found or inactive",
        )

    target_url = link.full_deeplink
    if not target_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing target deeplink for short link",
        )

    # Basic device detection and metadata for logging
    user_agent = request.headers.get("user-agent", "")
    device_info = DeviceDetector.parse_user_agent(user_agent)
    device_type = device_info.get("device_type")
    os = device_info.get("os")

    redirect_log = LinkRedirectLog(
        link_id=link.id,
        short_code=short_code,
        user_agent=user_agent,
        ip_address=request.client.host if request.client else "127.0.0.1",
        referer=request.headers.get("referer"),
        device_type=device_type,
        os=os,
        country=None,
        city=None,
        timestamp=datetime.utcnow(),
    )

    session.add(redirect_log)
    link.click_count += 1
    link.redirect_count += 1
    await session.commit()

    logger.info(f"Redirecting short link {short_code} to {target_url}")

    return RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)


@router.get(
    "/api/links/{link_id}",
    response_model=DiplinkResponse,
    summary="Get link details",
    description="Retrieve details of a generated link",
)
async def get_link(
    link_id: str,
    session: AsyncSession = Depends(get_session),
) -> DiplinkResponse:
    stmt = select(GeneratedLink).where(GeneratedLink.id == link_id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    return DiplinkResponse(
        id=link.id,
        short_code=link.short_code,
        short_url=f"https://{link.domain_name}/l/{link.short_code}",
        full_deeplink=link.full_deeplink,
        qr_code_url=link.qr_code_data,
        marketplace=link.marketplace,
        external_product_id=link.external_product_id,
        utm_metadata={
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
        },
        created_at=link.created_at,
    )


@router.get(
    "/api/links/short/{short_code}",
    response_model=DiplinkResponse,
    summary="Get link by short code",
    description="Retrieve link details using short code",
)
async def get_link_by_short_code(
    short_code: str,
    session: AsyncSession = Depends(get_session),
) -> DiplinkResponse:
    stmt = select(GeneratedLink).where(GeneratedLink.short_code == short_code)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    return DiplinkResponse(
        id=link.id,
        short_code=link.short_code,
        short_url=f"https://{link.domain_name}/l/{link.short_code}",
        full_deeplink=link.full_deeplink,
        qr_code_url=link.qr_code_data,
        marketplace=link.marketplace,
        external_product_id=link.external_product_id,
        utm_metadata={
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "utm_term": link.utm_term,
            "utm_content": link.utm_content,
        },
        created_at=link.created_at,
    )


@router.post(
    "/api/links/{link_id}/deactivate",
    summary="Deactivate a link",
    description="Stop tracking and disable a previously generated link",
)
async def deactivate_link(
    link_id: str,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(GeneratedLink).where(GeneratedLink.id == link_id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    link.is_active = False
    await session.commit()

    return {"message": "Link deactivated"}
