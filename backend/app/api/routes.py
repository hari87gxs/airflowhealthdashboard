"""
API Endpoints for the Health Dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime
from loguru import logger

from app.models import (
    DashboardResponse,
    DomainDetailResponse,
    DagRunSummary,
    HealthCheckResponse,
    TimeRange
)
from app.service import health_service
from app.airflow_client import airflow_client
from app.cache import cache_service
from app import __version__

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the status of the application and its dependencies.
    """
    airflow_status = "connected" if await airflow_client.test_connection() else "disconnected"
    cache_status = cache_service.get_status()
    
    return HealthCheckResponse(
        status="healthy" if airflow_status == "connected" else "degraded",
        version=__version__,
        airflow_connection=airflow_status,
        cache_status=cache_status,
        timestamp=datetime.utcnow()
    )


@router.get("/domains", response_model=DashboardResponse)
async def get_domains(
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for filtering DAG runs"
    )
):
    """
    Get all domain summaries with aggregated health metrics.
    
    This is the main endpoint for the dashboard view.
    Returns aggregated health statistics for each business domain/tag.
    """
    try:
        logger.info(f"GET /domains - time_range: {time_range.value}")
        return await health_service.get_dashboard_data(time_range)
    except Exception as e:
        logger.error(f"Error fetching domains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch domain data: {str(e)}")


@router.get("/domains/{domain_tag}", response_model=DomainDetailResponse)
async def get_domain_detail(
    domain_tag: str,
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for filtering DAG runs"
    )
):
    """
    Get detailed information for a specific domain.
    
    Returns:
    - Domain summary
    - List of all DAGs in the domain with their health metrics
    """
    try:
        logger.info(f"GET /domains/{domain_tag} - time_range: {time_range.value}")
        return await health_service.get_domain_detail(domain_tag, time_range)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching domain detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch domain detail: {str(e)}")


@router.get("/domains/{domain_tag}/dags/{dag_id}/runs", response_model=List[DagRunSummary])
async def get_dag_runs(
    domain_tag: str,
    dag_id: str,
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for filtering DAG runs"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of runs to return")
):
    """
    Get recent runs for a specific DAG.
    
    Returns a list of DAG run summaries with direct links to the Airflow UI.
    """
    try:
        logger.info(f"GET /domains/{domain_tag}/dags/{dag_id}/runs - time_range: {time_range.value}")
        return await health_service.get_dag_runs(dag_id, time_range, limit)
    except Exception as e:
        logger.error(f"Error fetching DAG runs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch DAG runs: {str(e)}")


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cached data.
    
    This is useful for forcing a fresh fetch from Airflow API.
    Note: This should be protected in production.
    """
    try:
        logger.info("POST /cache/clear - Clearing all cache")
        success = await cache_service.clear_all()
        return {"status": "success" if success else "failed", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
