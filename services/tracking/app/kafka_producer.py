import os
from aiokafka import AIOKafkaProducer

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        )
        await _producer.start()
    return _producer


async def produce_event(topic: str, key: str, value: str) -> None:
    producer = await get_producer()
    await producer.send_and_wait(
        topic,
        key=key.encode(),
        value=value.encode(),
    )
