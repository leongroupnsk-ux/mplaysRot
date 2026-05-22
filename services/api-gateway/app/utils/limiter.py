"""
Rate-limiter singleton (slowapi + Redis storage).

Import the `limiter` object in routers; wire `_rate_limit_exceeded_handler`
and `app.state.limiter` in main.py.

Key function respects X-Forwarded-For set by nginx so limits are per real
client IP, not the nginx container address.  The header is trusted only when
the request arrives from 127.0.0.1 or a private RFC-1918 range (nginx runs
inside the same Docker network).
"""
from ipaddress import ip_address, IPv4Network, IPv6Network
from typing import Union
from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

_TRUSTED_PROXIES: list[Union[IPv4Network, IPv6Network]] = [
    IPv4Network("127.0.0.0/8"),
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
]


def _real_ip(request: Request) -> str:
    """Return the real client IP, trusting X-Forwarded-For from private proxies."""
    connecting_ip = request.client.host if request.client else "127.0.0.1"
    try:
        addr = ip_address(connecting_ip)
        from_trusted = any(addr in net for net in _TRUSTED_PROXIES)
    except ValueError:
        from_trusted = False

    if from_trusted:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # Header may contain a comma-separated chain; first entry is the client.
            client_ip = forwarded_for.split(",")[0].strip()
            try:
                ip_address(client_ip)  # validate before using
                return client_ip
            except ValueError:
                pass

    return connecting_ip


def _build_limiter() -> Limiter:
    from app.config import settings

    storage_uri = settings.redis_url
    return Limiter(key_func=_real_ip, storage_uri=storage_uri)


limiter = _build_limiter()


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )
