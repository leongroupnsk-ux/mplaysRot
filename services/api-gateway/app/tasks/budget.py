"""
Проверка бюджетов кампаний: если потрачено ≥ 90% бюджета — уведомление warning,
если ≥ 100% — уведомление budget_depleted.
Запускается Celery beat каждые 2 часа.
"""
import asyncio
import logging

from app.celery import celery

log = logging.getLogger(__name__)


@celery.task(name="app.tasks.budget.check_budgets", bind=True, max_retries=2)
def check_budgets(self):
    try:
        asyncio.get_event_loop().run_until_complete(_check_budgets())
    except Exception as exc:
        log.error("Budget check failed: %s", exc)
        raise self.retry(exc=exc, countdown=600)


async def _check_budgets():
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.db.postgres import AsyncSessionLocal
    from app.db.clickhouse import get_clickhouse
    from app.models.campaign import Campaign
    from app.models.segments import Notification

    ch = get_clickhouse()

    # Суммарный spend по campaign_id за текущий месяц
    spend_rows = ch.query("""
        SELECT campaign_id, sum(spend) AS total_spend
        FROM ad_stats
        WHERE toStartOfMonth(stat_date) = toStartOfMonth(today())
        GROUP BY campaign_id
    """).result_rows

    spend_by_campaign: dict[str, float] = {
        str(cid): float(spend)
        for cid, spend in spend_rows
    }

    if not spend_by_campaign:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Campaign).where(
                Campaign.id.in_(spend_by_campaign.keys()),
                Campaign.budget.is_not(None),
                Campaign.is_active.is_(True),
            )
        )
        campaigns = result.scalars().all()

        now = datetime.now(timezone.utc)
        notifications_to_add: list[Notification] = []

        for campaign in campaigns:
            spent = spend_by_campaign.get(str(campaign.id), 0.0)
            budget = float(campaign.budget)
            pct = spent / budget * 100 if budget > 0 else 0.0

            if pct < 90:
                continue

            notif_type = "budget_depleted" if pct >= 100 else "low_roas"
            title = (
                f"Бюджет исчерпан: «{campaign.name}»"
                if pct >= 100
                else f"Бюджет на исходе: «{campaign.name}»"
            )
            body = (
                f"Расходы кампании составили {spent:,.0f} ₽ из {budget:,.0f} ₽ "
                f"({pct:.0f}%). Новые показы могут быть приостановлены."
            )

            # Не дублируем уведомление — проверяем за последние 6 часов
            existing = await db.execute(
                select(Notification).where(
                    Notification.campaign_id == campaign.id,
                    Notification.type == notif_type,
                    Notification.created_at >= now - timedelta(hours=6),
                )
            )
            if existing.scalar_one_or_none():
                continue

            notifications_to_add.append(Notification(
                user_id=campaign.user_id,
                campaign_id=campaign.id,
                type=notif_type,
                title=title,
                body=body,
                payload={
                    "spent": spent,
                    "budget": budget,
                    "pct": round(pct, 1),
                },
            ))

        if notifications_to_add:
            db.add_all(notifications_to_add)
            await db.commit()
            log.info("Created %d budget notifications", len(notifications_to_add))
