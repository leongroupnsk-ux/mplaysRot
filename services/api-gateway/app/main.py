import logging
import yaml
import sentry_sdk
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.routers import auth, campaigns, analytics, attribution, segments, webhooks, connections, integrations, stores, products, notifications, admin, billing, logistics, blog, blog_admin, links, domains, domains_admin, canvas
from app.utils.limiter import limiter, _rate_limit_exceeded_handler

logger = logging.getLogger(__name__)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)


def _run_migrations() -> None:
    """Применяет все непримененные Alembic-миграции при старте.
    Запускается через subprocess чтобы избежать конфликта event loop с asyncpg.
    """
    import subprocess, sys
    alembic_ini = str(Path(__file__).resolve().parents[1] / "alembic.ini")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", alembic_ini, "upgrade", "head"],
            cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("Alembic migrations OK")
        else:
            logger.warning("Alembic migration warning: %s", result.stderr[-500:])
    except Exception as exc:
        logger.warning("Could not run Alembic migrations: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_migrations()
    yield

_OPENAPI_SPEC_PATH = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"


def _load_openapi() -> dict:
    if _OPENAPI_SPEC_PATH.exists():
        with _OPENAPI_SPEC_PATH.open() as f:
            return yaml.safe_load(f)
    return get_openapi(title="Attribly API", version="0.1.0", routes=app.routes)


app = FastAPI(
    title="Attribly API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    redirect_slashes=False,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.openapi = _load_openapi  # type: ignore[method-assign]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

# All business routes live under /v1/; webhooks and health stay at root level.
app.include_router(auth.router,          prefix="/v1/auth",          tags=["auth"])
app.include_router(campaigns.router,     prefix="/v1/campaigns",     tags=["campaigns"])
app.include_router(analytics.router,     prefix="/v1/analytics",     tags=["analytics"])
app.include_router(attribution.router,   prefix="/v1/attribution",   tags=["attribution"])
app.include_router(segments.router,      prefix="/v1/segments",      tags=["segments"])
app.include_router(connections.router,   prefix="/v1/connections",   tags=["connections"])
app.include_router(integrations.router,  prefix="/v1/integrations",  tags=["integrations"])
app.include_router(stores.router,        prefix="/v1/stores",        tags=["stores"])
app.include_router(products.router,      prefix="/v1/products",      tags=["products"])
app.include_router(notifications.router, prefix="/v1/notifications", tags=["notifications"])
app.include_router(webhooks.router,      prefix="/webhooks",         tags=["webhooks"])
app.include_router(admin.router,         prefix="/admin",            tags=["admin"])
app.include_router(billing.router,       prefix="/v1/billing",       tags=["billing"])
app.include_router(logistics.router,     prefix="/v1/logistics",     tags=["logistics"])
app.include_router(blog.router,          prefix="/v1/blog",          tags=["blog"])
app.include_router(blog_admin.router,    prefix="/admin/blog",       tags=["blog-admin"])
app.include_router(links.router,         prefix="/v1/links",         tags=["links"])
app.include_router(domains.router,       prefix="/v1/domains",       tags=["domains"])
app.include_router(domains_admin.router, prefix="/admin/domains",    tags=["admin-domains"])
app.include_router(canvas.router,        prefix="/v1/canvas",         tags=["canvas"])


_UPLOADS_DIR = Path("/tmp/blog_uploads")
_UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads/blog", StaticFiles(directory=str(_UPLOADS_DIR)), name="blog-uploads")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "api-gateway"}
