"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import router
from app import __version__
from app.service import HealthService
from app.models import TimeRange
from app.scheduler import scheduled_reporter
from datetime import time

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Global background task references
background_task = None
scheduler_task = None
health_service = None


async def precompute_failure_analysis():
    """Background task to precompute and cache failure analysis."""
    global health_service
    
    if not health_service:
        health_service = HealthService()
    
    logger.info("Starting background precomputation of failure analysis...")
    
    while True:
        try:
            # Precompute for different time ranges
            for time_range in [TimeRange.HOURS_24, TimeRange.DAYS_7, TimeRange.DAYS_30]:
                logger.info(f"Precomputing failure analysis for {time_range.value}")
                await health_service.get_failure_analysis(time_range)
                logger.info(f"Successfully cached failure analysis for {time_range.value}")
                
        except Exception as e:
            logger.error(f"Error in background failure analysis precomputation: {e}")
        
        # Wait for the refresh interval
        await asyncio.sleep(settings.refresh_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global background_task, scheduler_task
    
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting Airflow Health Dashboard API v{__version__}")
    logger.info(f"Airflow URL: {settings.airflow_base_url}")
    logger.info(f"API Prefix: {settings.api_prefix}")
    logger.info(f"Cache TTL: {settings.cache_ttl_seconds}s")
    logger.info(f"Refresh Interval: {settings.refresh_interval_seconds}s")
    logger.info(f"Slack Notifications: {'Enabled' if settings.slack_enabled else 'Disabled'}")
    logger.info(f"Scheduled Reports: {'Enabled' if settings.scheduled_reports_enabled else 'Disabled'}")
    if settings.scheduled_reports_enabled:
        logger.info(f"Morning Report: {settings.morning_report_hour:02d}:{settings.morning_report_minute:02d}")
        logger.info(f"Evening Report: {settings.evening_report_hour:02d}:{settings.evening_report_minute:02d}")
    logger.info("=" * 60)
    
    # Start background task for failure analysis precomputation
    background_task = asyncio.create_task(precompute_failure_analysis())
    logger.info("Started background failure analysis precomputation task")
    
    # Start scheduler if enabled
    if settings.scheduled_reports_enabled and settings.slack_enabled:
        logger.info("Starting scheduled reports task")
        
        # Configure scheduled reporter with settings
        scheduled_reporter.morning_time = time(
            settings.morning_report_hour,
            settings.morning_report_minute
        )
        scheduled_reporter.evening_time = time(
            settings.evening_report_hour,
            settings.evening_report_minute
        )
        scheduled_reporter.dashboard_url = settings.dashboard_url
        
        scheduler_task = asyncio.create_task(scheduled_reporter.run_scheduler())
        logger.info("Scheduled reports task started")
    else:
        if not settings.scheduled_reports_enabled:
            logger.info("Scheduled reports disabled via configuration")
        if not settings.slack_enabled:
            logger.info("Slack notifications disabled - scheduled reports will not run")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Airflow Health Dashboard API")
    
    # Stop scheduler
    if scheduler_task:
        scheduled_reporter.stop()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled successfully")
    
    # Stop background task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background task cancelled successfully")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Airflow Health Dashboard API",
    description="Read-only monitoring dashboard for Airflow DAGs grouped by business domains",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
