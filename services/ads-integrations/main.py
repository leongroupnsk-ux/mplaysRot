"""
Main entry point for Ads Integrations Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from config import settings
from routers import integrations, audiences, performance

# Create FastAPI app
app = FastAPI(
    title="Attribly Ads Integrations API",
    description="Manage and sync ads from Yandex Direct, VK Ads, Telegram Ads, VK Blogger",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(audiences.router, prefix="/api/v1/audiences", tags=["audiences"])
app.include_router(performance.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "environment": settings.app_env,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Attribly Ads Integrations",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.app_env == "development",
    )
