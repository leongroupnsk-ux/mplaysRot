"""
Main entry point for AI Assistant Service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from config import settings
from routers import assistant

# Create FastAPI app
app = FastAPI(
    title="Attribly AI Assistant API",
    description="OpenAI-powered AI assistant for logistics and marketing recommendations",
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
app.include_router(assistant.router, prefix="/api/v1/ai", tags=["ai"])


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
        "service": "Attribly AI Assistant",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=settings.app_env == "development",
    )
