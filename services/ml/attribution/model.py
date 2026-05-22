"""
Вероятностная модель атрибуции на CatBoost.

Для маркетплейсов с UTM (Ozon, Яндекс.Маркет) используется строгая атрибуция
(confidence=1.0). Для WB и Amazon — эта ML-модель.
"""
import logging
import uuid
from datetime import date, timedelta, datetime, timezone

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from services.ml.attribution.features import (
    build_feature_matrix, load_training_data, CandidatePair, FEATURE_COLS,
)
from services.ml.shared.store import save_joblib, load_joblib, model_exists
from services.ml.shared.ch_client import get_ch

log = logging.getLogger(__name__)

_MODEL_NAME = "attribution_catboost"
_CONFIDENCE_THRESHOLD = 0.5
_ATTRIBUTION_WINDOW_HOURS = 14 * 24  # 14 дней по умолчанию


def train() -> CatBoostClassifier:
    X, y = load_training_data()
    if len(X) < 100:
        log.warning("Not enough training data (%d rows), skipping retrain", len(X))
        if model_exists(_MODEL_NAME):
            return load_joblib(_MODEL_NAME)
        return _default_model()

    model = CatBoostClassifier(
        iterations=500,
        learning_rate=0.05,
        depth=6,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=42,
        verbose=False,
    )
    model.fit(X, y, eval_set=(X, y), use_best_model=False)
    save_joblib(_MODEL_NAME, model)
    log.info("Attribution model trained on %d samples, AUC=%.4f",
             len(X), _eval_auc(model, X, y))
    return model


def _eval_auc(model, X, y) -> float:
    from sklearn.metrics import roc_auc_score
    proba = model.predict_proba(X)[:, 1]
    return float(roc_auc_score(y, proba))


def _default_model() -> CatBoostClassifier:
    """Простая заглушка если данных нет — линейная эвристика по времени."""
    m = CatBoostClassifier(iterations=10, verbose=False)
    X = pd.DataFrame([[h, 0, 0, 0, 0.05, np.log1p(h), int(h<=24), int(h<=72), int(h<=168)]
                      for h in range(1, 11)], columns=FEATURE_COLS)
    y = pd.Series([1,1,1,1,0,0,0,0,0,0])
    m.fit(X, y)
    return m


def load() -> CatBoostClassifier:
    if not model_exists(_MODEL_NAME):
        log.info("No saved attribution model, training default")
        return _default_model()
    return load_joblib(_MODEL_NAME)


def run_strict_attribution(window_days: int = 14) -> int:
    """
    Строгая атрибуция для Ozon и Яндекс.Маркет.

    Если заказ пришёл по трекинг-ссылке, marketplace сохраняет trax_id в UTM-параметрах
    (поле utm_trax_id в marketplace_orders). Join по trax_id даёт confidence=1.0 без ML.
    Обрабатываем только заказы, у которых utm_trax_id уже заполнен ETL-пайплайном.
    """
    ch = get_ch()

    orders = ch.query(f"""
        SELECT order_id, marketplace, user_id, product_id,
               order_amount, ordered_at, utm_trax_id
        FROM marketplace_orders
        WHERE marketplace IN ('ozon', 'yandex_market')
          AND utm_trax_id != ''
          AND attributed_trax_id = ''
          AND ordered_at >= now() - INTERVAL {window_days} DAY
        LIMIT 10000
    """).result_rows

    if not orders:
        return 0

    attributed = 0
    for order in orders:
        order_id, marketplace, user_id, product_id, amount, ordered_at, trax_id = order

        # Находим кампанию по trax_id через таблицу кликов (или напрямую через Redis недоступен)
        link_row = ch.query("""
            SELECT campaign_id, ad_platform
            FROM clicks
            WHERE trax_id = %(trax_id)s
            ORDER BY ts DESC
            LIMIT 1
        """, parameters={"trax_id": trax_id}).result_rows

        if not link_row:
            # trax_id есть в заказе, но нет соответствующего клика — пишем без click_at
            _write_strict_attribution(
                ch, order_id=order_id, marketplace=marketplace,
                user_id=user_id, product_id=product_id, amount=float(amount),
                ordered_at=str(ordered_at), trax_id=trax_id,
                campaign_id="", ad_platform="", click_at=str(ordered_at),
            )
        else:
            campaign_id, ad_platform = link_row[0]
            # Находим последний клик с этим trax_id до момента заказа
            click_row = ch.query("""
                SELECT ts FROM clicks
                WHERE trax_id = %(trax_id)s
                  AND ts <= %(ordered_at)s
                ORDER BY ts DESC
                LIMIT 1
            """, parameters={"trax_id": trax_id, "ordered_at": str(ordered_at)}).result_rows

            click_at = str(click_row[0][0]) if click_row else str(ordered_at)
            _write_strict_attribution(
                ch, order_id=order_id, marketplace=marketplace,
                user_id=user_id, product_id=product_id, amount=float(amount),
                ordered_at=str(ordered_at), trax_id=trax_id,
                campaign_id=campaign_id, ad_platform=ad_platform, click_at=click_at,
            )

        attributed += 1

    log.info("Strict attribution: %d orders attributed (Ozon/YM)", attributed)
    return attributed


def _write_strict_attribution(ch, *, order_id, marketplace, user_id, product_id,
                               amount, ordered_at, trax_id, campaign_id, ad_platform,
                               click_at):
    try:
        ordered_dt = datetime.fromisoformat(ordered_at.replace("Z", "+00:00"))
        click_dt = datetime.fromisoformat(click_at.replace("Z", "+00:00"))
        hours_to_order = (ordered_dt - click_dt).total_seconds() / 3600
    except Exception:
        hours_to_order = 0.0

    ch.insert("attributions", [[
        str(uuid.uuid4()),
        order_id, marketplace, campaign_id, trax_id, ad_platform,
        user_id, product_id, amount,
        click_at, ordered_at,
        max(0.0, hours_to_order),
        "strict", 1.0, "utm_join_v1",
    ]], column_names=[
        "attribution_id", "order_id", "marketplace", "campaign_id", "trax_id",
        "ad_platform", "user_id", "product_id", "order_amount",
        "click_at", "order_at", "hours_to_order",
        "attribution_method", "confidence", "model_version",
    ])


def run_attribution(window_days: int = 14) -> int:
    """
    Основная задача: берёт неатрибутированные заказы WB/Amazon за окно,
    ищет кандидатные клики, скорит моделью, записывает результат в ClickHouse.
    Возвращает количество новых атрибуций.
    """
    ch = get_ch()
    model = load()
    window_hours = window_days * 24

    # Заказы без атрибуции из WB/Amazon
    orders = ch.query(f"""
        SELECT order_id, marketplace, user_id, product_id,
               order_amount, ordered_at, '' AS region
        FROM marketplace_orders
        WHERE marketplace IN ('wildberries', 'amazon')
          AND attributed_trax_id = ''
          AND ordered_at >= now() - INTERVAL {window_days} DAY
        LIMIT 10000
    """).result_rows

    if not orders:
        return 0

    attributed = 0
    for order in orders:
        order_id, marketplace, user_id, product_id, amount, ordered_at, region_order = order

        # Кандидатные клики в окне атрибуции
        clicks = ch.query(f"""
            SELECT trax_id, campaign_id, ad_platform, ts,
                   country AS region, device_type
            FROM clicks
            WHERE user_id = %(user_id)s
              AND ts <= %(ordered_at)s
              AND ts >= %(ordered_at)s - INTERVAL {window_days} DAY
            ORDER BY ts DESC
            LIMIT 20
        """, parameters={"user_id": user_id, "ordered_at": str(ordered_at)}).result_rows

        if not clicks:
            continue

        pairs = [
            CandidatePair(
                trax_id=c[0], campaign_id=c[1], ad_platform=c[2], marketplace=marketplace,
                click_at=str(c[3]), order_id=order_id, order_at=str(ordered_at),
                product_id_click="", product_id_order=product_id,
                region_click=c[4], region_order=region_order, device_click=c[5],
            )
            for c in clicks
        ]

        X = build_feature_matrix(pairs)
        proba = model.predict_proba(X)[:, 1]
        best_idx = int(np.argmax(proba))
        best_conf = float(proba[best_idx])

        if best_conf < _CONFIDENCE_THRESHOLD:
            continue

        best = pairs[best_idx]
        _write_attribution(ch, best, order_id, marketplace, product_id, amount,
                           str(ordered_at), best_conf)
        attributed += 1

    log.info("Attributed %d orders in this run", attributed)
    return attributed


def _write_attribution(ch, pair: CandidatePair, order_id, marketplace,
                       product_id, amount, ordered_at, confidence):
    from services.ml.shared.store import load_joblib
    ch.insert("attributions", [[
        str(uuid.uuid4()),
        order_id, marketplace, pair.campaign_id, pair.trax_id, pair.ad_platform,
        "", product_id, float(amount),
        pair.click_at, ordered_at,
        float((datetime.fromisoformat(ordered_at.replace("Z", "+00:00")) -
               datetime.fromisoformat(pair.click_at.replace("Z", "+00:00"))).total_seconds() / 3600),
        "probabilistic", confidence, "catboost_v1",
    ]], column_names=[
        "attribution_id", "order_id", "marketplace", "campaign_id", "trax_id",
        "ad_platform", "user_id", "product_id", "order_amount",
        "click_at", "order_at", "hours_to_order",
        "attribution_method", "confidence", "model_version",
    ])
