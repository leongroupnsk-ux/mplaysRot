import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

from uploader import run_worker


if __name__ == "__main__":
    asyncio.run(run_worker())
