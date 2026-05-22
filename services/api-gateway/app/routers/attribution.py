from fastapi import APIRouter, Depends, Query
from datetime import date

from app.db.clickhouse import get_clickhouse
from app.models.user import User
from app.schemas.attribution import AttributionLogEntry
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/log", response_model=list[AttributionLogEntry])
async def get_attribution_log(
    date_from: date = Query(...),
    date_to: date = Query(...),
    campaign_id: str | None = Query(None),
    marketplace: str | None = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    where_parts = [
        "user_id = {user_id:String}",
        "toDate(order_at) >= {date_from:Date}",
        "toDate(order_at) <= {date_to:Date}",
        "confidence >= {min_confidence:Float32}",
    ]
    params: dict = {
        "user_id": str(current_user.id),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "min_confidence": min_confidence,
        "limit": limit,
        "offset": offset,
    }
    if campaign_id:
        where_parts.append("campaign_id = {campaign_id:String}")
        params["campaign_id"] = campaign_id
    if marketplace:
        where_parts.append("marketplace = {marketplace:String}")
        params["marketplace"] = marketplace

    where_clause = " AND ".join(where_parts)

    rows = ch.query(
        f"""
        SELECT
            order_id,
            campaign_id,
            trax_id,
            marketplace,
            ad_platform,
            product_id,
            toFloat64(order_amount)  AS order_amount,
            click_at,
            order_at,
            hours_to_order           AS time_to_order_hours,
            confidence,
            attribution_method
        FROM attributions
        WHERE {where_clause}
        ORDER BY order_at DESC
        LIMIT {{limit:UInt32}}
        OFFSET {{offset:UInt32}}
        """,
        parameters=params,
    ).result_rows

    return [
        AttributionLogEntry(
            order_id=row[0],
            campaign_id=row[1],
            trax_id=row[2],
            marketplace=row[3],
            ad_platform=row[4],
            product_id=row[5],
            order_amount=float(row[6]),
            click_at=row[7],
            order_at=row[8],
            time_to_order_hours=float(row[9]),
            confidence=float(row[10]),
            attribution_method=row[11],
        )
        for row in rows
    ]
