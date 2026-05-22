from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta

from app.db.clickhouse import get_clickhouse
from app.models.user import User
from app.schemas.analytics import (
    OverviewResponse, PeriodMetrics,
    FunnelResponse, FunnelStep,
    GeoResponse,
    TimeSeriesPoint,
    TopCreativeRow,
    ClickToOrderBucket,
)
from app.utils.deps import get_current_user

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_div(a: float, b: float) -> float:
    return a / b if b > 0 else 0.0


def _query_period_metrics(ch, user_id: str, d_from: date, d_to: date,
                           marketplace: str | None, ad_platform: str | None) -> PeriodMetrics:
    where = ["user_id = {uid:String}", "stat_date >= {df:Date}", "stat_date <= {dt:Date}"]
    params: dict = {"uid": user_id, "df": d_from.isoformat(), "dt": d_to.isoformat()}
    if marketplace:
        where.append("marketplace = {mp:String}")
        params["mp"] = marketplace
    if ad_platform:
        where.append("ad_platform = {ap:String}")
        params["ap"] = ad_platform

    rows = ch.query(
        f"SELECT sum(spend), sum(attributed_revenue), sum(attributed_orders), sum(clicks) "
        f"FROM campaign_daily_stats WHERE {' AND '.join(where)}",
        parameters=params,
    ).result_rows

    if not rows or rows[0][0] is None:
        spend, revenue, orders, clicks = 0.0, 0.0, 0, 0
    else:
        spend   = float(rows[0][0] or 0)
        revenue = float(rows[0][1] or 0)
        orders  = int(rows[0][2] or 0)
        clicks  = int(rows[0][3] or 0)

    return PeriodMetrics(
        total_spend=spend,
        total_revenue=revenue,
        roas=_safe_div(revenue, spend),
        attributed_orders=orders,
        click_to_order_rate=_safe_div(orders, clicks),
        avg_order_value=_safe_div(revenue, orders),
    )


# ── /overview ─────────────────────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    date_from: date = Query(...),
    date_to: date = Query(...),
    marketplace: str | None = Query(None),
    ad_platform: str | None = Query(None),
    compare: bool = Query(False),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    uid = str(current_user.id)
    current = _query_period_metrics(ch, uid, date_from, date_to, marketplace, ad_platform)

    previous = None
    if compare:
        span = (date_to - date_from).days + 1
        prev_to = date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=span - 1)
        previous = _query_period_metrics(ch, uid, prev_from, prev_to, marketplace, ad_platform)

    return OverviewResponse(
        date_from=date_from,
        date_to=date_to,
        **current.model_dump(),
        previous_period=previous,
    )


# ── /timeseries ───────────────────────────────────────────────────────────────

@router.get("/timeseries", response_model=list[TimeSeriesPoint])
async def get_timeseries(
    date_from: date = Query(...),
    date_to: date = Query(...),
    marketplace: str | None = Query(None),
    ad_platform: str | None = Query(None),
    campaign_id: str | None = Query(None),
    granularity: str = Query("day", pattern="^(day|week)$"),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    where = ["user_id = {uid:String}", "stat_date >= {df:Date}", "stat_date <= {dt:Date}"]
    params: dict = {
        "uid": str(current_user.id),
        "df": date_from.isoformat(),
        "dt": date_to.isoformat(),
    }
    if marketplace:
        where.append("marketplace = {mp:String}")
        params["mp"] = marketplace
    if ad_platform:
        where.append("ad_platform = {ap:String}")
        params["ap"] = ad_platform
    if campaign_id:
        where.append("campaign_id = {cid:String}")
        params["cid"] = campaign_id

    trunc = "toMonday(stat_date)" if granularity == "week" else "stat_date"

    rows = ch.query(
        f"""
        SELECT
            toString({trunc})          AS dt,
            sum(spend)                 AS spend,
            sum(attributed_revenue)    AS revenue,
            sum(clicks)                AS clicks,
            sum(attributed_orders)     AS orders
        FROM campaign_daily_stats
        WHERE {' AND '.join(where)}
        GROUP BY dt
        ORDER BY dt
        """,
        parameters=params,
    ).result_rows

    result = []
    for dt, spend, revenue, clicks, orders in rows:
        spend   = float(spend   or 0)
        revenue = float(revenue or 0)
        clicks  = int(clicks    or 0)
        orders  = int(orders    or 0)
        result.append(TimeSeriesPoint(
            date=str(dt),
            spend=spend,
            revenue=revenue,
            clicks=clicks,
            orders=orders,
            roas=_safe_div(revenue, spend),
        ))
    return result


# ── /funnel ───────────────────────────────────────────────────────────────────

@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel(
    campaign_id: str = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    rows = ch.query(
        """
        SELECT sum(clicks), sum(favorites), sum(cart_adds), sum(attributed_orders)
        FROM campaign_daily_stats
        WHERE campaign_id = {cid:String}
          AND stat_date >= {df:Date}
          AND stat_date <= {dt:Date}
        """,
        parameters={
            "cid": campaign_id,
            "df": date_from.isoformat(),
            "dt": date_to.isoformat(),
        },
    ).result_rows

    if not rows or rows[0][0] is None:
        clicks, favorites, cart_adds, orders = 0, 0, 0, 0
    else:
        clicks    = int(rows[0][0] or 0)
        favorites = int(rows[0][1] or 0)
        cart_adds = int(rows[0][2] or 0)
        orders    = int(rows[0][3] or 0)

    steps = [
        FunnelStep(name="Клики",     count=clicks,    conversion_rate=1.0),
        FunnelStep(name="Избранное", count=favorites,  conversion_rate=_safe_div(favorites, clicks)),
        FunnelStep(name="Корзина",   count=cart_adds,  conversion_rate=_safe_div(cart_adds, clicks)),
        FunnelStep(name="Заказы",    count=orders,     conversion_rate=_safe_div(orders, clicks)),
    ]
    return FunnelResponse(campaign_id=campaign_id, steps=steps)


# ── /geo ──────────────────────────────────────────────────────────────────────

@router.get("/geo", response_model=list[GeoResponse])
async def get_geo(
    date_from: date = Query(...),
    date_to: date = Query(...),
    campaign_id: str | None = Query(None),
    marketplace: str | None = Query(None),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    where_click = [
        "toDate(c.ts) BETWEEN {df:Date} AND {dt:Date}",
        "c.region != ''",
    ]
    where_attr = ["toDate(order_at) BETWEEN {df:Date} AND {dt:Date}"]
    params: dict = {"df": date_from.isoformat(), "dt": date_to.isoformat()}

    if campaign_id:
        where_click.append("c.campaign_id = {cid:String}")
        where_attr.append("campaign_id = {cid:String}")
        params["cid"] = campaign_id
    if marketplace:
        where_click.append("c.marketplace = {mp:String}")
        params["mp"] = marketplace

    rows = ch.query(
        f"""
        SELECT
            c.region,
            count()                                     AS clicks,
            countIf(a.attribution_id != '')             AS orders,
            sumIf(toFloat64(a.order_amount), a.attribution_id != '') AS revenue
        FROM clicks AS c
        LEFT JOIN (
            SELECT trax_id, attribution_id, order_amount
            FROM attributions
            WHERE {' AND '.join(where_attr)}
        ) AS a ON c.trax_id = a.trax_id
        WHERE {' AND '.join(where_click)}
        GROUP BY c.region
        ORDER BY clicks DESC
        LIMIT 50
        """,
        parameters=params,
    ).result_rows

    return [
        GeoResponse(
            region=region,
            clicks=int(clicks or 0),
            orders=int(orders or 0),
            revenue=float(revenue or 0),
            conversion_rate=_safe_div(int(orders or 0), int(clicks or 0)),
        )
        for region, clicks, orders, revenue in rows
    ]


# ── /top-creatives ────────────────────────────────────────────────────────────

@router.get("/top-creatives", response_model=list[TopCreativeRow])
async def get_top_creatives(
    date_from: date = Query(...),
    date_to: date = Query(...),
    ad_platform: str | None = Query(None),
    campaign_id: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    where = [
        "user_id = {uid:String}",
        "stat_date >= {df:Date}",
        "stat_date <= {dt:Date}",
    ]
    params: dict = {
        "uid": str(current_user.id),
        "df": date_from.isoformat(),
        "dt": date_to.isoformat(),
        "lim": limit,
    }
    if ad_platform:
        where.append("ad_platform = {ap:String}")
        params["ap"] = ad_platform
    if campaign_id:
        where.append("campaign_id = {cid:String}")
        params["cid"] = campaign_id

    rows = ch.query(
        f"""
        SELECT
            any(external_ad_id)         AS external_ad_id,
            any(ad_name)                AS ad_name,
            ad_platform,
            sum(spend)                  AS spend,
            sum(clicks)                 AS clicks,
            sum(attributed_orders)      AS orders,
            if(sum(spend) > 0, sum(attributed_revenue) / sum(spend), 0) AS roas
        FROM ad_stats
        WHERE {' AND '.join(where)}
        GROUP BY ad_platform, external_ad_id
        ORDER BY spend DESC
        LIMIT {{lim:UInt32}}
        """,
        parameters=params,
    ).result_rows

    return [
        TopCreativeRow(
            external_ad_id=str(row[0] or ""),
            ad_name=str(row[1] or ""),
            ad_platform=str(row[2] or ""),
            spend=float(row[3] or 0),
            clicks=int(row[4] or 0),
            orders=int(row[5] or 0),
            roas=float(row[6] or 0),
        )
        for row in rows
    ]


# ── /click-to-order-distribution ─────────────────────────────────────────────

@router.get("/click-to-order-distribution", response_model=list[ClickToOrderBucket])
async def get_click_to_order_distribution(
    date_from: date = Query(...),
    date_to: date = Query(...),
    campaign_id: str | None = Query(None),
    ch=Depends(get_clickhouse),
    current_user: User = Depends(get_current_user),
):
    where = [
        "user_id = {uid:String}",
        "toDate(order_at) >= {df:Date}",
        "toDate(order_at) <= {dt:Date}",
    ]
    params: dict = {
        "uid": str(current_user.id),
        "df": date_from.isoformat(),
        "dt": date_to.isoformat(),
    }
    if campaign_id:
        where.append("campaign_id = {cid:String}")
        params["cid"] = campaign_id

    rows = ch.query(
        f"""
        SELECT
            multiIf(
                hours_to_order < 1,   '< 1ч',
                hours_to_order < 6,   '1–6ч',
                hours_to_order < 24,  '6–24ч',
                hours_to_order < 72,  '1–3д',
                hours_to_order < 168, '3–7д',
                '> 7д'
            ) AS bucket,
            count() AS cnt
        FROM attributions
        WHERE {' AND '.join(where)}
        GROUP BY bucket
        ORDER BY min(hours_to_order)
        """,
        parameters=params,
    ).result_rows

    total = sum(int(r[1] or 0) for r in rows) or 1
    return [
        ClickToOrderBucket(
            bucket_label=str(row[0]),
            count=int(row[1] or 0),
            pct=round(int(row[1] or 0) / total * 100, 1),
        )
        for row in rows
    ]
