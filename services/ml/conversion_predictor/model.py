"""
Предиктивная модель конверсии.

Обучение: LogisticRegression → экспорт в ONNX.
Инференс: onnxruntime (легковесный, без sklearn в продакшне).

Признаки доступны в момент клика (real-time):
- platform: рекламная площадка
- device: тип устройства
- hour_of_day: час клика
- day_of_week: день недели
- is_weekend: выходной
- platform_hist_rate: исторический CR площадки
- campaign_cr: исторический CR кампании
- geo_cr: исторический CR региона
"""
import logging
from datetime import datetime, timezone

import numpy as np
import onnxruntime as ort
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from services.ml.shared.store import save_onnx, load_onnx_path, save_joblib, load_joblib, model_exists
from services.ml.shared.ch_client import get_ch

log = logging.getLogger(__name__)

_MODEL_NAME = "conversion_predictor"
_SCALER_NAME = "conversion_scaler"

FEATURE_COLS = [
    "platform_enc", "device_enc",
    "hour_of_day", "day_of_week", "is_weekend",
    "platform_hist_rate", "campaign_cr", "geo_cr",
]

_PLATFORM_MAP = {
    "yandex_direct": 0, "vk_ads": 1, "vk_blogger": 2,
    "telegram_ads": 3, "messenger_max": 4,
}
_DEVICE_MAP = {"desktop": 0, "mobile": 1, "tablet": 2}


def train() -> None:
    """Обучает модель и экспортирует в ONNX."""
    import pandas as pd

    ch = get_ch()
    rows = ch.query("""
        SELECT
            c.ad_platform,
            c.device_type,
            toHour(c.ts)                           AS hour_of_day,
            toDayOfWeek(c.ts)                      AS day_of_week,
            toDayOfWeek(c.ts) IN (6, 7)            AS is_weekend,
            coalesce(ph.hist_rate, 0.05)           AS platform_hist_rate,
            coalesce(cc.campaign_cr, 0.05)         AS campaign_cr,
            coalesce(gc.geo_cr, 0.05)              AS geo_cr,
            isNotNull(a.order_id)                  AS label
        FROM clicks c
        LEFT JOIN (
            SELECT ad_platform, avg(label) AS hist_rate
            FROM attribution_features WHERE feature_date >= today() - 60
            GROUP BY ad_platform
        ) ph ON ph.ad_platform = c.ad_platform
        LEFT JOIN (
            SELECT campaign_id, countIf(label=1) / count() AS campaign_cr
            FROM attribution_features WHERE feature_date >= today() - 60
            GROUP BY campaign_id
        ) cc ON cc.campaign_id = c.campaign_id
        LEFT JOIN (
            SELECT country, avg(label) AS geo_cr
            FROM attribution_features af
            JOIN clicks cl ON cl.trax_id = af.trax_id
            WHERE af.feature_date >= today() - 60
            GROUP BY country
        ) gc ON gc.country = c.country
        LEFT JOIN attributions a ON a.trax_id = c.trax_id AND a.confidence >= 0.5
        WHERE c.ts >= now() - INTERVAL 90 DAY
        LIMIT 1000000
    """).result_rows

    if len(rows) < 500:
        log.warning("Not enough data to train conversion predictor (%d rows)", len(rows))
        return

    df = pd.DataFrame(rows, columns=FEATURE_COLS + ["label"])
    df["platform_enc"] = df["ad_platform"].map(_PLATFORM_MAP).fillna(-1)
    df["device_enc"] = df["device_type"].map(_DEVICE_MAP).fillna(-1)
    df = df.drop(columns=["ad_platform", "device_type"], errors="ignore")

    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["label"].values.astype(int)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, C=1.0, class_weight="balanced")),
    ])
    pipe.fit(X, y)

    # Экспорт в ONNX
    initial_type = [("float_input", FloatTensorType([None, len(FEATURE_COLS)]))]
    onnx_model = convert_sklearn(pipe, initial_types=initial_type)
    save_onnx(_MODEL_NAME, onnx_model)
    log.info("Conversion predictor trained and exported to ONNX (%d rows)", len(rows))


class ConversionPredictor:
    """RT-инференс через onnxruntime — без sklearn в памяти."""

    def __init__(self):
        self._session: ort.InferenceSession | None = None

    def _get_session(self) -> ort.InferenceSession:
        if self._session is None:
            path = load_onnx_path(_MODEL_NAME)
            self._session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        return self._session

    def score(self, features: dict) -> float:
        """
        Принимает словарь признаков клика, возвращает вероятность конверсии (0–1).
        Используется в tracking-сервисе при каждом клике (опционально).
        """
        try:
            session = self._get_session()
        except FileNotFoundError:
            return 0.05  # fallback до первого обучения

        x = np.array([[
            _PLATFORM_MAP.get(features.get("ad_platform", ""), -1),
            _DEVICE_MAP.get(features.get("device_type", ""), -1),
            features.get("hour_of_day", 12),
            features.get("day_of_week", 1),
            features.get("is_weekend", 0),
            features.get("platform_hist_rate", 0.05),
            features.get("campaign_cr", 0.05),
            features.get("geo_cr", 0.05),
        ]], dtype=np.float32)

        input_name = session.get_inputs()[0].name
        proba = session.run(None, {input_name: x})[1]  # [labels, probas]
        return float(proba[0][1])


# Синглтон для переиспользования в tracking-сервисе
predictor = ConversionPredictor()
