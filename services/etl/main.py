import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

from consumer import ETLConsumer


async def main() -> None:
    consumer = ETLConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
