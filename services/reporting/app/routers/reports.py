"""
Report generation endpoints.

POST /reports/export
    type: attribution | overview | campaigns
    date_from, date_to: ISO-8601 date strings
    campaign_id: optional UUID filter (attribution only)

Returns a presigned MinIO URL valid for 1 hour.
"""
import csv
import io
import logging
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.ch_client import query
from app.deps import get_current_user_id
from app.storage import upload_and_sign

router = APIRouter()
log = logging.getLogger(__name__)

ReportType = Literal["attribution", "overview", "campaigns"]


class ExportResponse(BaseModel):
    url: str
    filename: str
    expires_at: str
    rows: int


def _date_param(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, detail=f"Invalid date: {s}")


# ─── Attribution report ───────────────────────────────────────────────────────

def _build_attribution_csv(user_id: str, date_from: date, date_to: date,
                            campaign_id: str | None) -> tuple[bytes, int]:
    filters = [
        "user_id = {user_id:String}",
        "order_at >= {date_from:Date}",
        "order_at <= {date_to:Date}",
    ]
    params: dict = {"user_id": user_id, "date_from": str(date_from), "date_to": str(date_to)}

    if campaign_id:
        filters.append("campaign_id = {campaign_id:String}")
        params["campaign_id"] = campaign_id

    sql = f"""
        SELECT
            attribution_id,
            order_id,
            campaign_id,
            trax_id,
            marketplace,
            ad_platform,
            product_id,
            order_amount,
            click_at,
            order_at,
            hours_to_order,
            confidence,
            attribution_method,
            model_version
        FROM attributions
        WHERE {' AND '.join(filters)}
        ORDER BY order_at DESC
        LIMIT 100000
    """
    result = query(sql, params)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "attribution_id", "order_id", "campaign_id", "trax_id",
        "marketplace", "ad_platform", "product_id", "order_amount",
        "click_at", "order_at", "hours_to_order", "confidence",
        "attribution_method", "model_version",
    ])
    writer.writerows(result.result_rows)

    return buf.getvalue().encode("utf-8-sig"), len(result.result_rows)


# ─── Overview / summary report ────────────────────────────────────────────────

def _build_overview_csv(user_id: str, date_from: date, date_to: date) -> tuple[bytes, int]:
    sql = """
        SELECT
            toDate(stat_date)           AS date,
            ad_platform,
            sum(impressions)            AS impressions,
            sum(clicks)                 AS clicks,
            sum(spend)                  AS spend,
            sum(conversions)            AS conversions,
            sum(conversion_value)       AS revenue,
            if(sum(spend) > 0, round(sum(conversion_value) / sum(spend), 4), 0) AS roas
        FROM ad_stats
        WHERE user_id = {user_id:String}
          AND stat_date >= {date_from:Date}
          AND stat_date <= {date_to:Date}
        GROUP BY date, ad_platform
        ORDER BY date, ad_platform
    """
    result = query(sql, {
        "user_id": user_id,
        "date_from": str(date_from),
        "date_to": str(date_to),
    })

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "ad_platform", "impressions", "clicks",
                     "spend", "conversions", "revenue", "roas"])
    writer.writerows(result.result_rows)
    return buf.getvalue().encode("utf-8-sig"), len(result.result_rows)


# ─── Campaign performance report ─────────────────────────────────────────────

def _build_campaigns_csv(user_id: str, date_from: date, date_to: date) -> tuple[bytes, int]:
    sql = """
        SELECT
            a.campaign_id,
            count()                                 AS attributed_orders,
            sum(a.order_amount)                     AS revenue,
            avg(a.confidence)                       AS avg_confidence,
            countIf(a.attribution_method = 'strict') AS strict_count
        FROM attributions a
        WHERE a.user_id = {user_id:String}
          AND a.order_at >= {date_from:Date}
          AND a.order_at <= {date_to:Date}
        GROUP BY a.campaign_id
        ORDER BY revenue DESC
    """
    result = query(sql, {
        "user_id": user_id,
        "date_from": str(date_from),
        "date_to": str(date_to),
    })

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["campaign_id", "attributed_orders", "revenue",
                     "avg_confidence", "strict_count"])
    writer.writerows(result.result_rows)
    return buf.getvalue().encode("utf-8-sig"), len(result.result_rows)


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/export", response_model=ExportResponse)
async def export_report(
    type: ReportType = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
    campaign_id: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    d_from = _date_param(date_from)
    d_to = _date_param(date_to)

    if d_from > d_to:
        raise HTTPException(400, detail="date_from must be ≤ date_to")

    try:
        if type == "attribution":
            data, rows = _build_attribution_csv(user_id, d_from, d_to, campaign_id)
        elif type == "overview":
            data, rows = _build_overview_csv(user_id, d_from, d_to)
        else:
            data, rows = _build_campaigns_csv(user_id, d_from, d_to)
    except Exception as exc:
        log.error("Report generation failed: %s", exc)
        raise HTTPException(500, detail="Report generation failed")

    ts = datetime.now(timezone.utc)
    filename = f"{type}_{date_from}_{date_to}_{ts.strftime('%Y%m%dT%H%M%S')}.csv"
    key = f"reports/{user_id}/{filename}"

    try:
        url = upload_and_sign(key, data)
    except Exception as exc:
        log.error("MinIO upload failed: %s", exc)
        raise HTTPException(500, detail="Storage upload failed")

    from app.config import settings
    expires_at = ts.replace(second=ts.second + settings.report_presigned_ttl).isoformat()

    return ExportResponse(url=url, filename=filename, rows=rows, expires_at=expires_at)
