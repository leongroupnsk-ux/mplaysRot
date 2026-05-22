import clickhouse_connect
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

_client = None


def get_ch():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def query(sql: str, params: dict | None = None):
    return get_ch().query(sql, parameters=params or {})
