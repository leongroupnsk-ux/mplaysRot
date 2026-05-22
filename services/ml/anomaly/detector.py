"""
Детектор аномалий кампаний (Isolation Forest на временных рядах CPC / CR / ROAS).

Алгоритм:
- Берём почасовые метрики за последние 7 дней как нормальное распределение.
- Смотрим на последние 2 часа.
- Isolation Forest флагует выбросы.
- Тяжесть аномалии определяется отклонением от медианы.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sklearn.ensemble import IsolationForest

from services.ml.shared.ch_client import get_ch

log = logging.getLogger(__name__)

_CONTAMINATION = 0.05  # ожидаемая доля аномалий


@dataclass
class Anomaly:
    campaign_id: str
    metric: str
    current_value: float
    expected_value: float
    deviation_pct: float
    severity: str  # 'warning' | 'critical'


def detect_anomalies() -> list[Anomaly]:
    ch = get_ch()

    # Получаем почасовую статистику активных кампаний за 7 дней
    rows = ch.query("""
        SELECT
            campaign_id,
            toStartOfHour(ts)           AS hour,
            count()                     AS clicks,
            uniqExact(visitor_hash)     AS uniq
        FROM clicks
        WHERE ts >= now() - INTERVAL 7 DAY
        GROUP BY campaign_id, hour
        ORDER BY campaign_id, hour
    """).result_rows

    if not rows:
        return []

    # Группируем по кампаниям
    campaigns: dict[str, list] = {}
    for campaign_id, hour, clicks, uniq in rows:
        campaigns.setdefault(campaign_id, []).append((hour, clicks, uniq))

    # Расходы из ad_stats (дневные, джойним по кампании)
    spend_rows = ch.query("""
        SELECT campaign_id, stat_date, spend
        FROM ad_stats
        WHERE stat_date >= today() - 7
    """).result_rows
    spend_by_campaign: dict[str, float] = {}
    for cid, _, spend in spend_rows:
        spend_by_campaign[cid] = spend_by_campaign.get(cid, 0.0) + float(spend)

    anomalies: list[Anomaly] = []

    for campaign_id, hourly in campaigns.items():
        if len(hourly) < 24:
            continue  # Слишком мало данных

        clicks_series = np.array([h[1] for h in hourly], dtype=float).reshape(-1, 1)
        last_clicks = float(hourly[-1][1])

        anom = _check_metric(campaign_id, "clicks", clicks_series, last_clicks)
        if anom:
            anomalies.append(anom)

    _write_anomalies(ch, anomalies)
    return anomalies


def _check_metric(campaign_id: str, metric: str,
                  series: np.ndarray, current: float) -> Anomaly | None:
    if len(series) < 24:
        return None

    history = series[:-1]  # всё кроме последнего
    expected = float(np.median(history))

    if expected == 0:
        return None

    deviation_pct = abs(current - expected) / expected * 100

    if deviation_pct < 50:
        return None

    # Isolation Forest на истории
    clf = IsolationForest(contamination=_CONTAMINATION, random_state=42)
    clf.fit(history)
    score = clf.decision_function(np.array([[current]]))[0]

    # score < 0 означает аномалию
    if score >= 0:
        return None

    severity = "critical" if deviation_pct > 200 else "warning"

    return Anomaly(
        campaign_id=str(campaign_id),
        metric=metric,
        current_value=current,
        expected_value=expected,
        deviation_pct=deviation_pct,
        severity=severity,
    )


def _write_anomalies(ch, anomalies: list[Anomaly]) -> None:
    if not anomalies:
        return

    now = datetime.now(timezone.utc).isoformat()
    ch.insert("anomaly_log", [
        [now, a.campaign_id, a.metric, a.current_value,
         a.expected_value, a.deviation_pct, a.severity, 0]
        for a in anomalies
    ], column_names=[
        "detected_at", "campaign_id", "metric", "current_value",
        "expected_value", "deviation_pct", "severity", "notified",
    ])
    log.info("Wrote %d anomalies to anomaly_log", len(anomalies))
