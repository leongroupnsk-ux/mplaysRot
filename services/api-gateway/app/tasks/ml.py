import logging
import sys
import os

from app.celery import celery

log = logging.getLogger(__name__)

# ML-сервисы находятся в соседнем пакете — добавляем корень проекта в PYTHONPATH
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@celery.task(name="app.tasks.ml.run_attribution_model", bind=True, max_retries=2)
def run_attribution_model(self, window_days: int = 14):
    """Пересчитывает атрибуции WB/Amazon (probabilistic) за окно window_days дней."""
    try:
        from services.ml.attribution.model import run_attribution
        count = run_attribution(window_days=window_days)
        log.info("Attribution run complete: %d new attributions", count)
        return {"attributed": count}
    except Exception as exc:
        log.error("Attribution model failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)


@celery.task(name="app.tasks.ml.run_strict_attribution", bind=True, max_retries=2)
def run_strict_attribution_task(self, window_days: int = 14):
    """Строгая атрибуция для Ozon/ЯМ по trax_id из UTM-параметров заказа."""
    try:
        from services.ml.attribution.model import run_strict_attribution
        count = run_strict_attribution(window_days=window_days)
        log.info("Strict attribution complete: %d orders attributed", count)
        return {"attributed": count}
    except Exception as exc:
        log.error("Strict attribution failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)


@celery.task(name="app.tasks.ml.retrain_all_models", bind=True, max_retries=1)
def retrain_all_models(self):
    """Переобучает атрибуционную модель и предиктор конверсии."""
    results = {}

    try:
        from services.ml.attribution.model import train as train_attribution
        train_attribution()
        results["attribution"] = "ok"
    except Exception as exc:
        log.error("Attribution retrain failed: %s", exc)
        results["attribution"] = f"error: {exc}"

    try:
        from services.ml.conversion_predictor.model import train as train_predictor
        train_predictor()
        results["conversion_predictor"] = "ok"
    except Exception as exc:
        log.error("Conversion predictor retrain failed: %s", exc)
        results["conversion_predictor"] = f"error: {exc}"

    return results


@celery.task(name="app.tasks.ml.detect_campaign_anomalies", bind=True, max_retries=3)
def detect_campaign_anomalies(self):
    """Запускает детектор аномалий и создаёт уведомления для пользователей."""
    try:
        from services.ml.anomaly.detector import detect_anomalies
        anomalies = detect_anomalies()

        if anomalies:
            _create_anomaly_notifications(anomalies)

        log.info("Anomaly detection complete: %d anomalies found", len(anomalies))
        return {"anomalies": len(anomalies)}
    except Exception as exc:
        log.error("Anomaly detection failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@celery.task(name="app.tasks.ml.build_lookalike_segment")
def build_lookalike_segment(task_id: str, campaign_id: str, ad_platform: str,
                            min_roas: float = 3.0, scale: int = 5):
    """
    Строит look-alike сегмент и передаёт visitor_hashes в задачу загрузки.
    Запускается из tasks/segmentation.py после готовности seed.
    """
    try:
        from services.ml.lookalike.model import build_segment
        segment = build_segment(campaign_id=campaign_id, min_roas=min_roas, scale=scale)
        log.info("Lookalike built: %d hashes for campaign %s", len(segment.visitor_hashes), campaign_id)
        return {
            "task_id": task_id,
            "visitor_hashes": segment.visitor_hashes,
            "ad_platform": ad_platform,
        }
    except Exception as exc:
        log.error("Lookalike build failed for campaign %s: %s", campaign_id, exc)
        raise


def _create_anomaly_notifications(anomalies) -> None:
    """Создаёт уведомления в PostgreSQL для каждой аномальной кампании."""
    import asyncio
    from app.db.postgres import AsyncSessionLocal
    from app.models.segments import Notification
    from app.models.campaign import Campaign
    from sqlalchemy import select

    # campaign_id → (user_id, ad_platform) collected during PG writes so we can
    # back-fill the new anomaly_log columns and mark rows notified in one pass.
    enrichment: dict[str, tuple[str, str]] = {}

    async def _write_pg():
        async with AsyncSessionLocal() as db:
            for anomaly in anomalies:
                result = await db.execute(
                    select(Campaign).where(Campaign.id == anomaly.campaign_id)
                )
                campaign = result.scalar_one_or_none()
                if not campaign:
                    continue

                enrichment[str(anomaly.campaign_id)] = (
                    str(campaign.user_id),
                    str(campaign.ad_platform or ""),
                )

                notif = Notification(
                    user_id=campaign.user_id,
                    campaign_id=campaign.id,
                    type="anomaly_detected",
                    title=f"Аномалия в кампании «{campaign.name}»",
                    body=(
                        f"Метрика {anomaly.metric} отклонилась на "
                        f"{anomaly.deviation_pct:.0f}% от нормы. "
                        f"Текущее значение: {anomaly.current_value:.1f}, "
                        f"ожидалось: {anomaly.expected_value:.1f}."
                    ),
                    payload={
                        "metric": anomaly.metric,
                        "current": anomaly.current_value,
                        "expected": anomaly.expected_value,
                        "deviation_pct": anomaly.deviation_pct,
                        "severity": anomaly.severity,
                    },
                )
                db.add(notif)
            await db.commit()

    asyncio.get_event_loop().run_until_complete(_write_pg())

    if not enrichment:
        return

    # Mark anomalies as notified in ClickHouse and back-fill user_id / ad_platform.
    # ALTER TABLE UPDATE is a lightweight mutation — eventual on replicas, safe here.
    try:
        _PROJECT_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../..")
        )
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)

        from services.ml.shared.ch_client import get_ch

        ch = get_ch()
        campaign_ids = list(enrichment.keys())
        ids_sql = ", ".join(f"'{cid}'" for cid in campaign_ids)
        ch.command(
            f"ALTER TABLE anomaly_log UPDATE notified = 1 "
            f"WHERE campaign_id IN ({ids_sql}) AND notified = 0"
        )
        log.info("Marked %d campaign anomaly groups as notified in ClickHouse", len(campaign_ids))
    except Exception as exc:
        # Non-fatal: PG notifications are already committed; CH mutation can be retried.
        log.warning("Could not mark anomaly_log rows as notified: %s", exc)
