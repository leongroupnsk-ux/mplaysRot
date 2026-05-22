"""
Kafka consumer с батч-буфером и flush по размеру или по таймауту.

Логика:
- Читаем из трёх топиков (clicks, orders, events) в одном consumer group.
- Буферизируем сообщения по типу.
- Флашим в ClickHouse при достижении batch_size или flush_interval секунд.
- После успешного flush делаем commit offset.
- Retry через tenacity при сбоях CH.
"""
import asyncio
import json
import logging
import time
from collections import defaultdict

from aiokafka import AIOKafkaConsumer
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from normalizer import normalize_click, normalize_funnel_event, normalize_order
from ch_writer import get_client, insert_clicks, insert_funnel_events, insert_orders

log = logging.getLogger(__name__)

TOPICS = [
    settings.kafka_topic_clicks,
    settings.kafka_topic_orders,
    settings.kafka_topic_events,
]


class ETLConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._ch = get_client()

        # Буферы по топику
        self._buffers: dict[str, list[dict]] = defaultdict(list)
        self._last_flush = time.monotonic()

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            *TOPICS,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        )
        await self._consumer.start()
        log.info("ETL consumer started, topics: %s", TOPICS)

        try:
            await self._run()
        finally:
            await self._consumer.stop()

    async def _run(self) -> None:
        assert self._consumer is not None

        async for msg in self._consumer:
            self._handle_message(msg.topic, msg.value)

            total_buffered = sum(len(v) for v in self._buffers.values())
            elapsed = time.monotonic() - self._last_flush

            if total_buffered >= settings.batch_size or elapsed >= settings.flush_interval:
                await self._flush()
                await self._consumer.commit()

    def _handle_message(self, topic: str, payload: dict) -> None:
        if topic == settings.kafka_topic_clicks:
            row = normalize_click(payload)
            if row:
                self._buffers["clicks"].append(row)

        elif topic == settings.kafka_topic_events:
            row = normalize_funnel_event(payload)
            if row:
                self._buffers["events"].append(row)

        elif topic == settings.kafka_topic_orders:
            row = normalize_order(payload)
            if row:
                self._buffers["orders"].append(row)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
    async def _flush(self) -> None:
        clicks = self._buffers.pop("clicks", [])
        events = self._buffers.pop("events", [])
        orders = self._buffers.pop("orders", [])

        try:
            if clicks:
                insert_clicks(self._ch, clicks)
            if events:
                insert_funnel_events(self._ch, events)
            if orders:
                insert_orders(self._ch, orders)
        except Exception as exc:
            # Возвращаем данные в буфер для повтора
            self._buffers["clicks"].extend(clicks)
            self._buffers["events"].extend(events)
            self._buffers["orders"].extend(orders)
            log.error("CH insert failed, will retry: %s", exc)
            raise

        self._last_flush = time.monotonic()
        log.debug("Flush done: clicks=%d events=%d orders=%d",
                  len(clicks), len(events), len(orders))
