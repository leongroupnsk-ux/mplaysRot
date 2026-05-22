"""
Look-alike модель.

Алгоритм:
1. Строим профиль покупателей из seed-аудитории (аттрибутированные заказы кампании).
2. Строим профиль фоновой аудитории (случайная выборка кликов без конверсии).
3. Обучаем бинарный классификатор: seed (1) vs фон (0).
4. Скорим всех посетителей без конверсии, берём топ-N% по вероятности.
5. Возвращаем visitor_hash → внешние ID для загрузки в рекламный кабинет.
"""
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder

from services.ml.shared.store import save_joblib, load_joblib, model_exists
from services.ml.shared.ch_client import get_ch

log = logging.getLogger(__name__)

_FEATURE_COLS = [
    "avg_order_amount", "order_count",
    "platform_enc", "device_enc",
    "top_geo_enc", "days_since_first_click",
]


@dataclass
class LookalikeSegment:
    visitor_hashes: list[str]
    model_version: str = "gbm_v1"


def build_segment(campaign_id: str, min_roas: float = 3.0, scale: int = 5) -> LookalikeSegment:
    """
    Строит look-alike сегмент для кампании.
    scale: 1–10, масштаб (1 = топ 1%, 10 = топ 10% похожих).
    """
    ch = get_ch()
    top_pct = scale / 10.0

    seed_df = _load_seed_profiles(ch, campaign_id, min_roas)
    background_df = _load_background_profiles(ch, campaign_id)

    if len(seed_df) < 10:
        log.warning("Seed too small (%d rows) for campaign %s", len(seed_df), campaign_id)
        return LookalikeSegment(visitor_hashes=[])

    model, encoders = _train(seed_df, background_df)
    candidates_df = _load_candidate_profiles(ch, campaign_id)

    if candidates_df.empty:
        return LookalikeSegment(visitor_hashes=[])

    X_cand = _encode(candidates_df, encoders)
    proba = model.predict_proba(X_cand)[:, 1]
    threshold = np.quantile(proba, 1 - top_pct)
    selected = candidates_df[proba >= threshold]["visitor_hash"].tolist()

    log.info("Lookalike: seed=%d, candidates=%d, selected=%d (top %.0f%%)",
             len(seed_df), len(candidates_df), len(selected), top_pct * 100)

    return LookalikeSegment(visitor_hashes=selected)


def _load_seed_profiles(ch, campaign_id: str, min_roas: float) -> pd.DataFrame:
    rows = ch.query("""
        SELECT
            c.visitor_hash,
            avg(a.order_amount)           AS avg_order_amount,
            count(a.order_id)             AS order_count,
            any(c.ad_platform)            AS platform,
            any(c.device_type)            AS device,
            any(c.country)                AS top_geo,
            dateDiff('day', min(c.ts), now()) AS days_since_first_click
        FROM clicks c
        JOIN attributions a ON a.trax_id = c.trax_id
        WHERE c.campaign_id = %(cid)s
          AND a.confidence >= 0.5
        GROUP BY c.visitor_hash
        HAVING avg_order_amount > 0
        LIMIT 50000
    """, parameters={"cid": campaign_id}).result_rows

    return pd.DataFrame(rows, columns=[
        "visitor_hash", "avg_order_amount", "order_count",
        "platform", "device", "top_geo", "days_since_first_click",
    ])


def _load_background_profiles(ch, campaign_id: str) -> pd.DataFrame:
    rows = ch.query("""
        SELECT
            visitor_hash,
            0.0     AS avg_order_amount,
            0       AS order_count,
            any(ad_platform) AS platform,
            any(device_type) AS device,
            any(country)     AS top_geo,
            dateDiff('day', min(ts), now()) AS days_since_first_click
        FROM clicks
        WHERE campaign_id = %(cid)s
          AND visitor_hash NOT IN (
              SELECT DISTINCT c2.visitor_hash
              FROM clicks c2
              JOIN attributions a ON a.trax_id = c2.trax_id
              WHERE c2.campaign_id = %(cid)s
          )
        GROUP BY visitor_hash
        ORDER BY rand()
        LIMIT 200000
    """, parameters={"cid": campaign_id}).result_rows

    return pd.DataFrame(rows, columns=[
        "visitor_hash", "avg_order_amount", "order_count",
        "platform", "device", "top_geo", "days_since_first_click",
    ])


def _load_candidate_profiles(ch, campaign_id: str) -> pd.DataFrame:
    """Все посетители за последние 30 дней без конверсии."""
    rows = ch.query("""
        SELECT
            visitor_hash,
            0.0 AS avg_order_amount,
            0   AS order_count,
            any(ad_platform) AS platform,
            any(device_type) AS device,
            any(country)     AS top_geo,
            dateDiff('day', min(ts), now()) AS days_since_first_click
        FROM clicks
        WHERE ts >= now() - INTERVAL 30 DAY
          AND visitor_hash NOT IN (
              SELECT DISTINCT c2.visitor_hash
              FROM clicks c2
              JOIN attributions a ON a.trax_id = c2.trax_id
              WHERE c2.campaign_id = %(cid)s
          )
        GROUP BY visitor_hash
        LIMIT 1000000
    """, parameters={"cid": campaign_id}).result_rows

    return pd.DataFrame(rows, columns=[
        "visitor_hash", "avg_order_amount", "order_count",
        "platform", "device", "top_geo", "days_since_first_click",
    ])


def _train(seed_df: pd.DataFrame, bg_df: pd.DataFrame):
    seed_df = seed_df.copy()
    bg_df = bg_df.copy()
    seed_df["label"] = 1
    bg_df["label"] = 0

    combined = pd.concat([seed_df, bg_df], ignore_index=True)

    encoders: dict[str, LabelEncoder] = {}
    for col in ("platform", "device", "top_geo"):
        le = LabelEncoder()
        combined[f"{col}_enc"] = le.fit_transform(combined[col].fillna("unknown"))
        encoders[col] = le

    X = combined[_FEATURE_COLS].fillna(0)
    y = combined["label"]

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.1,
        subsample=0.8, random_state=42,
    )
    model.fit(X, y)
    return model, encoders


def _encode(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    df = df.copy()
    for col, le in encoders.items():
        known = set(le.classes_)
        df[f"{col}_enc"] = df[col].fillna("unknown").apply(
            lambda v: le.transform([v])[0] if v in known else 0
        )
    return df[_FEATURE_COLS].fillna(0)
