import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from config import settings
from app.database import init_db, close_db
from app.routers import deeplinks, redirector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LinkEngine API",
    description="Deeplinks and auto-landing generator for Attribly",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


# ───────────────────────────────────────────────────────────────────────
# Lifespan events
# ───────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize database and services on startup"""
    logger.info("🚀 LinkEngine API starting...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Close connections on shutdown"""
    logger.info("🛑 LinkEngine API shutting down...")
    await close_db()
    logger.info("✅ Connections closed")


# ───────────────────────────────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────────────────────────────

# Include routers
app.include_router(deeplinks)
app.include_router(redirector)


# Health check
@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "LinkEngine API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ───────────────────────────────────────────────────────────────────────
# Error handlers (can be extended)
# ───────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "detail": "Internal server error",
        "error_code": "INTERNAL_ERROR",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
