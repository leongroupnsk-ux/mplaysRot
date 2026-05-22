"""
Feature Engineering для атрибуционной модели.
Формирует матрицу признаков из пар (клик, заказ).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from services.ml.shared.features import (
    hours_between, geo_match, device_match, product_match,
)
from services.ml.shared.ch_client import get_ch

FEATURE_COLS = [
    "hours_since_click",
    "geo_match",
    "device_match",
    "product_match",
    "platform_hist_rate",
    "log_hours",
    "is_same_day",
    "is_within_3d",
    "is_within_7d",
]


@dataclass
class CandidatePair:
    trax_id: str
    campaign_id: str
    ad_platform: str
    marketplace: str
    click_at: str
    order_id: str
    order_at: str
    product_id_click: str
    product_id_order: str
    region_click: str
    region_order: str
    device_click: str


def build_feature_matrix(pairs: list[CandidatePair]) -> pd.DataFrame:
    ch = get_ch()

    # Историческая конверсионность каждой платформы
    hist = ch.query("""
        SELECT ad_platform, avg(label) AS hist_rate
        FROM attribution_features
        WHERE feature_date >= today() - 30
        GROUP BY ad_platform
    """).result_rows
    hist_rates = {row[0]: float(row[1]) for row in hist}

    rows = []
    for p in pairs:
        h = hours_between(p.click_at, p.order_at)
        rows.append({
            "hours_since_click": h,
            "geo_match": geo_match(p.region_click, p.region_order),
            "device_match": device_match(p.device_click, ""),
            "product_match": product_match(p.product_id_click, p.product_id_order),
            "platform_hist_rate": hist_rates.get(p.ad_platform, 0.05),
            "log_hours": float(np.log1p(h)),
            "is_same_day": int(h <= 24),
            "is_within_3d": int(h <= 72),
            "is_within_7d": int(h <= 168),
        })

    return pd.DataFrame(rows, columns=FEATURE_COLS)


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Загружает верифицированные и вероятностные пары из ClickHouse для обучения."""
    ch = get_ch()
    rows = ch.query("""
        SELECT
            hours_since_click, geo_match, device_match, product_match,
            platform_hist_rate,
            log(1 + hours_since_click) AS log_hours,
            hours_since_click <= 24    AS is_same_day,
            hours_since_click <= 72    AS is_within_3d,
            hours_since_click <= 168   AS is_within_7d,
            label
        FROM attribution_features
        WHERE feature_date >= today() - 90
          AND (is_confirmed = 1 OR label = 1)
        LIMIT 500000
    """).result_rows

    df = pd.DataFrame(rows, columns=FEATURE_COLS + ["label"])
    X = df[FEATURE_COLS]
    y = df["label"].astype(int)
    return X, y
