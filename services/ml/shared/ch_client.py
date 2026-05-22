import os
import clickhouse_connect

_client = None


def get_ch():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            database=os.getenv("CLICKHOUSE_DB", "attribly"),
            username=os.getenv("CLICKHOUSE_USER", "attribly"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        )
    return _client
