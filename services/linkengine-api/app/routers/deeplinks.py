from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session, GeneratedLink
from app.models import (
    GenerateDiplinkRequest,
    GenerateDiplinkResponse,
    VerifyProductRequest,
    VerifyProductResponse,
    MarketplaceType,
    DiplinkResponse,
    ErrorResponse,
)
from app.verifier import SKUVerifier
from app.deeplink_generator import DiplinkGenerator
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/links", tags=["deeplinks"])


@router.post(
    "/generate",
    response_model=DiplinkResponse,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Generate a deeplink",
    description="Generate a deeplink for a product with UTM tracking",
)
async def generate_deeplink(
    request: GenerateDiplinkRequest,
    session: AsyncSession = Depends(get_session),
) -> DiplinkResponse:
    """
    Generate a deeplink for a marketplace product.
    
    **Steps:**
    1. Verify product SKU belongs to the store
    2. Generate short code and tracking ID
    3. Create full deeplink with UTM parameters
    4. Generate QR code
    5. Save to database
    6. Return generated link
    
    **Errors:**
    - 400: Invalid product ID format or missing fields
    - 409: Product not found in store (verification failed)
    """

    # Validate product ID format
    if not DiplinkGenerator.validate_external_product_id(request.external_product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Артикул должен быть числовым значением",
        )

    # Step 1: Verify SKU belongs to store
    verifier = SKUVerifier()
    is_verified, verification_reason = await verifier.verify_sku(
        session=session,
        user_id=999,  # TODO: Get from auth token
        store_id=request.store_id,
        external_product_id=request.external_product_id,
        marketplace=request.marketplace,
        ip_address="0.0.0.0",  # TODO: Get from request
    )

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=verification_reason,
        )

    # Step 2: Generate tracking ID and short code
    trax_id = str(uuid4())
    short_code = DiplinkGenerator.generate_short_code()

    # Determine domain
    custom_domain = None
    if request.custom_domain_id:
        # TODO: Look up custom domain from DB
        custom_domain = None

    # Step 3-4: Generate deeplink
    deeplink_data = DiplinkGenerator.generate_deeplink(
        marketplace=request.marketplace,
        external_product_id=request.external_product_id,
        utm_metadata=request.utm_metadata,
        trax_id=trax_id,
        short_code=short_code,
        custom_domain=custom_domain,
    )

    # Step 5: Save to database
    link_id = str(uuid4())
    generated_link = GeneratedLink(
        id=link_id,
        short_code=short_code,
        user_id=999,  # TODO: From auth
        store_id=request.store_id,
        marketplace=request.marketplace.value,
        external_product_id=request.external_product_id,
        link_type="deeplink",
        custom_domain_id=request.custom_domain_id,
        domain_name=custom_domain or "attribly.ru",
        utm_source=request.utm_metadata.utm_source,
        utm_medium=request.utm_metadata.utm_medium,
        utm_campaign=request.utm_metadata.utm_campaign,
        utm_term=request.utm_metadata.utm_term,
        utm_content=request.utm_metadata.utm_content,
        title=request.title,
        full_deeplink=deeplink_data.get("full_deeplink"),
        qr_code_data=deeplink_data.get("qr_code_url"),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(generated_link)
    await session.commit()
    await session.refresh(generated_link)

    logger.info(
        f"Deeplink generated: {link_id} (short_code: {short_code}, store: {request.store_id})"
    )

    # Step 6: Return response
    return DiplinkResponse(
        id=link_id,
        short_code=short_code,
        short_url=deeplink_data["short_url"],
        full_deeplink=deeplink_data["full_deeplink"],
        qr_code_url=deeplink_data.get("qr_code_url"),
        marketplace=request.marketplace,
        external_product_id=request.external_product_id,
        utm_metadata=request.utm_metadata,
        created_at=generated_link.created_at,
    )


@router.post(
    "/verify-product",
    response_model=VerifyProductResponse,
    summary="Verify product belongs to store",
    description="Check if a product SKU is owned by a specific store",
)
async def verify_product(
    request: VerifyProductRequest,
    session: AsyncSession = Depends(get_session),
) -> VerifyProductResponse:
    """
    Verify that a product belongs to a store.
    
    Used before generating links to check product availability.
    """

    verifier = SKUVerifier()
    is_verified, reason = await verifier.verify_sku(
        session=session,
        user_id=999,  # TODO: From auth
        store_id=request.store_id,
        external_product_id=request.external_product_id,
        marketplace=request.marketplace,
    )

    return VerifyProductResponse(
        verified=is_verified,
        external_product_id=request.external_product_id,
        store_id=request.store_id,
        marketplace=request.marketplace,
        is_active=is_verified,
        reason=reason if not is_verified else None,
    )


@router.get(
    "/{link_id}",
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
    "/short/{short_code}",
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
    "/{link_id}/deactivate",
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
