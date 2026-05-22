"""
WebSocket notification service.

Clients connect to ws://<host>/ws?token=<access_jwt>
The service authenticates via JWT (same secret as api-gateway),
then streams real-time notifications published on Redis pub/sub.

When api-gateway creates a Notification, it also publishes to Redis:
  PUBLISH notifications <json_payload>

This service fans out matching messages to the correct user's WebSocket.
"""
import asyncio
import json
import logging
import sys

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from jose import JWTError, jwt

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

app = FastAPI(title="Attribly Notifications WS", docs_url=None, redoc_url=None)

# user_id → set of WebSocket connections
_connections: dict[str, set[WebSocket]] = {}


def _verify_token(token: str) -> str | None:
    """Returns user_id string or None if invalid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload["sub"]
    except JWTError:
        return None


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    user_id = _verify_token(token)
    if not user_id:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws.accept()
    _connections.setdefault(user_id, set()).add(ws)
    log.info("WS connected: user=%s (total=%d)", user_id, len(_connections[user_id]))

    try:
        while True:
            # Keep connection alive — client sends pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        _connections.get(user_id, set()).discard(ws)
        log.info("WS disconnected: user=%s", user_id)


async def _redis_listener():
    """Subscribes to Redis pub/sub and fans out messages to WebSocket clients."""
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(settings.notifications_channel)
    log.info("Redis listener subscribed to '%s'", settings.notifications_channel)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload: dict = json.loads(message["data"])
            user_id: str = payload.get("user_id", "")
            sockets = _connections.get(user_id, set())
            dead: set[WebSocket] = set()
            for ws in sockets:
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead.add(ws)
            sockets -= dead
        except Exception as exc:
            log.error("Listener error: %s", exc)


@app.on_event("startup")
async def startup():
    asyncio.create_task(_redis_listener())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notifications-ws", "connections": sum(len(v) for v in _connections.values())}
