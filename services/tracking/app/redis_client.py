import os
import redis.asyncio as aioredis

_pool = None


def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        password = os.getenv("REDIS_PASSWORD", "")
        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        auth = f":{password}@" if password else ""
        _pool = aioredis.ConnectionPool.from_url(
            f"redis://{auth}{host}:{port}/0", decode_responses=True
        )
    return aioredis.Redis(connection_pool=_pool)
