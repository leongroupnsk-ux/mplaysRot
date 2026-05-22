"""
ClickHouse client with retry + circuit-breaker.

- query()   → retries up to 3 times with exponential back-off on transient errors
- Circuit opens after 5 consecutive failures; re-probes every 30 s
- When open, returns an empty QueryResult instead of raising, so analytics
  endpoints degrade gracefully (empty charts) rather than returning 500
"""
import logging
import threading
import time
from typing import Any

import clickhouse_connect
from clickhouse_connect.driver.query import QueryResult

from app.config import settings

log = logging.getLogger(__name__)

# ── Circuit-breaker state ─────────────────────────────────────────────────────

_FAILURE_THRESHOLD = 5      # consecutive failures to open the circuit
_PROBE_INTERVAL_S  = 30     # seconds to wait before half-open probe

_lock = threading.Lock()
_failures = 0
_opened_at: float | None = None   # timestamp when circuit opened


def _is_open() -> bool:
    global _failures, _opened_at
    with _lock:
        if _opened_at is None:
            return False
        if time.monotonic() - _opened_at >= _PROBE_INTERVAL_S:
            # half-open: allow one probe through
            _opened_at = None
            return False
        return True


def _record_success() -> None:
    global _failures, _opened_at
    with _lock:
        _failures = 0
        _opened_at = None


def _record_failure() -> None:
    global _failures, _opened_at
    with _lock:
        _failures += 1
        if _failures >= _FAILURE_THRESHOLD and _opened_at is None:
            _opened_at = time.monotonic()
            log.error(
                "ClickHouse circuit OPENED after %d consecutive failures. "
                "Probing again in %ds.",
                _failures, _PROBE_INTERVAL_S,
            )


# ── Client singleton ──────────────────────────────────────────────────────────

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            connect_timeout=5,
            send_receive_timeout=30,
        )
    return _client


# ── Public interface ──────────────────────────────────────────────────────────

class _EmptyResult:
    """Returned when the circuit is open, so callers see an empty result."""
    result_rows: list = []


class _WrappedClient:
    """Thin wrapper that adds retry + circuit-breaker to ch.query() and ch.insert()."""

    _MAX_RETRIES = 3
    _RETRY_DELAYS = (0.5, 1.5, 4.0)

    def query(self, sql: str, parameters: dict[str, Any] | None = None) -> Any:
        if _is_open():
            log.warning("ClickHouse circuit is OPEN — returning empty result")
            return _EmptyResult()

        last_exc: Exception | None = None
        for attempt, delay in enumerate(self._RETRY_DELAYS):
            try:
                result = _get_client().query(sql, parameters=parameters or {})
                _record_success()
                return result
            except Exception as exc:
                last_exc = exc
                log.warning(
                    "ClickHouse query failed (attempt %d/%d): %s",
                    attempt + 1, self._MAX_RETRIES, exc,
                )
                if attempt < self._MAX_RETRIES - 1:
                    time.sleep(delay)

        _record_failure()
        log.error("ClickHouse query failed after %d retries: %s", self._MAX_RETRIES, last_exc)
        return _EmptyResult()

    def insert(self, table: str, data: list, column_names: list | None = None) -> None:
        if _is_open():
            log.warning("ClickHouse circuit is OPEN — dropping insert into %s", table)
            return

        try:
            _get_client().insert(table, data, column_names=column_names)
            _record_success()
        except Exception as exc:
            _record_failure()
            log.error("ClickHouse insert into %s failed: %s", table, exc)
            raise

    def command(self, sql: str) -> None:
        if _is_open():
            log.warning("ClickHouse circuit is OPEN — skipping command")
            return

        try:
            _get_client().command(sql)
            _record_success()
        except Exception as exc:
            _record_failure()
            log.error("ClickHouse command failed: %s", exc)
            raise


_wrapped = _WrappedClient()


def get_clickhouse() -> _WrappedClient:
    return _wrapped
