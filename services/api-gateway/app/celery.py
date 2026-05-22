from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "attribly",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.ingestion",
        "app.tasks.etl",
        "app.tasks.ml",
        "app.tasks.segmentation",
        "app.tasks.catalog",
        "app.tasks.budget",
    ],
)

celery.conf.beat_schedule = {
    # Сбор данных из рекламных кабинетов каждые 2 часа
    "fetch-ad-stats": {
        "task": "app.tasks.ingestion.fetch_all_ad_stats",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # Сбор заказов из маркетплейсов каждый час
    "fetch-marketplace-orders": {
        "task": "app.tasks.ingestion.fetch_all_marketplace_orders",
        "schedule": crontab(minute=15),
    },
    # Синхронизация каталога товаров каждые 2 часа
    "sync-catalog": {
        "task": "app.tasks.catalog.sync_all_catalogs",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # Строгая атрибуция Ozon/ЯМ каждый час — быстро, нет ML
    "run-strict-attribution": {
        "task": "app.tasks.ml.run_strict_attribution",
        "schedule": crontab(minute=30),
    },
    # Вероятностная атрибуция WB/Amazon раз в сутки в 03:00
    "run-attribution": {
        "task": "app.tasks.ml.run_attribution_model",
        "schedule": crontab(minute=0, hour=3),
    },
    # Переобучение ML-моделей раз в сутки в 04:00
    "retrain-models": {
        "task": "app.tasks.ml.retrain_all_models",
        "schedule": crontab(minute=0, hour=4),
    },
    # Проверка аномалий каждые 30 минут
    "detect-anomalies": {
        "task": "app.tasks.ml.detect_campaign_anomalies",
        "schedule": crontab(minute="*/30"),
    },
    # Проверка бюджетов каждые 2 часа
    "check-budgets": {
        "task": "app.tasks.budget.check_budgets",
        "schedule": crontab(minute=45, hour="*/2"),
    },
}
