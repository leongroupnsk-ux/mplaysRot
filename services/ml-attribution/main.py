"""
Main entry point for ML Attribution Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from config import settings
from routers import attribution, models

# Create FastAPI app
app = FastAPI(
    title="Attribly ML Attribution API",
    description="Attribution model inference and training service",
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
app.include_router(attribution.router, prefix="/api/v1/attribution", tags=["attribution"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])


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
        "service": "Attribly ML Attribution",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.app_env == "development",
    )
