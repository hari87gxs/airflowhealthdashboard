"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.api.routes import router
from app import __version__

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Create FastAPI app
app = FastAPI(
    title="Airflow Health Dashboard API",
    description="Read-only monitoring dashboard for Airflow DAGs grouped by business domains",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info(f"Starting Airflow Health Dashboard API v{__version__}")
    logger.info(f"Airflow URL: {settings.airflow_base_url}")
    logger.info(f"API Prefix: {settings.api_prefix}")
    logger.info(f"Cache TTL: {settings.cache_ttl_seconds}s")
    logger.info(f"Refresh Interval: {settings.refresh_interval_seconds}s")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Airflow Health Dashboard API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Airflow Health Dashboard API",
        "version": __version__,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
