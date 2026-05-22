import logging
import sys

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routers import reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

if settings.sentry_dsn if hasattr(settings, "sentry_dsn") else False:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)  # type: ignore

app = FastAPI(
    title="Attribly Reporting",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "reporting"}
