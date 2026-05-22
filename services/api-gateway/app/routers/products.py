from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User
from app.models.catalog import Product
from app.schemas.catalog import ProductResponse, ProductVariation, ProductSearchResponse
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query("", description="Поиск по названию или артикулу"),
    marketplace: str | None = Query(None),
    store_id: str | None = Query(None),
    include_out_of_stock: bool = Query(False),
    expand_variations: bool = Query(False, description="Подгрузить дочерние артикулы"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conditions = [
        Product.user_id == current_user.id,
        Product.is_archived.is_(False),
        Product.is_orphaned.is_(False),
        Product.parent_external_id.is_(None),  # только корневые в поиске
    ]
    if q:
        conditions.append(
            or_(
                Product.title.ilike(f"%{q}%"),
                Product.external_product_id.ilike(f"%{q}%"),
            )
        )
    if marketplace:
        conditions.append(Product.provider == marketplace)
    if store_id:
        conditions.append(Product.store_id == store_id)
    if not include_out_of_stock:
        conditions.append(Product.stock > 0)

    count_result = await db.execute(
        select(Product).where(*conditions)
    )
    total = len(count_result.scalars().all())

    result = await db.execute(
        select(Product)
        .where(*conditions)
        .order_by(Product.title)
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()

    items: list[ProductResponse] = []
    for p in products:
        variations: list[ProductVariation] = []
        if expand_variations and p.has_variations:
            var_result = await db.execute(
                select(Product).where(
                    Product.store_id == p.store_id,
                    Product.parent_external_id == p.external_product_id,
                    Product.is_archived.is_(False),
                )
            )
            variations = [
                ProductVariation(
                    external_product_id=v.external_product_id,
                    title=v.title,
                    stock=v.stock,
                )
                for v in var_result.scalars().all()
            ]

        items.append(ProductResponse(
            id=str(p.id),
            store_id=str(p.store_id),
            provider=p.provider,
            external_product_id=p.external_product_id,
            parent_external_id=p.parent_external_id,
            title=p.title,
            price=p.price,
            stock=p.stock,
            image_url=p.image_url,
            has_variations=p.has_variations,
            is_active=p.is_active,
            is_archived=p.is_archived,
            variations=variations,
        ))

    return ProductSearchResponse(items=items, total=total)
