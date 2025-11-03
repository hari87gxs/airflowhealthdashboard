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
from app.slack_service import slack_service
from app.scheduler import scheduled_reporter
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
    ),
    force_refresh: bool = Query(
        False,
        description="Force refresh from Airflow, bypassing cache"
    )
):
    """
    Get all domain summaries with aggregated health metrics.
    
    This is the main endpoint for the dashboard view.
    Returns aggregated health statistics for each business domain/tag.
    """
    try:
        logger.info(f"GET /domains - time_range: {time_range.value}, force_refresh: {force_refresh}")
        return await health_service.get_dashboard_data(time_range, force_refresh=force_refresh)
    except Exception as e:
        logger.error(f"Error fetching domains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch domain data: {str(e)}")


@router.get("/domains/{domain_tag}", response_model=DomainDetailResponse)
async def get_domain_detail(
    domain_tag: str,
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for filtering DAG runs"
    ),
    force_refresh: bool = Query(
        False,
        description="Force refresh from Airflow, bypassing cache"
    )
):
    """
    Get detailed information for a specific domain.
    
    Returns:
    - Domain summary
    - List of all DAGs in the domain with their health metrics
    """
    try:
        logger.info(f"GET /domains/{domain_tag} - time_range: {time_range.value}, force_refresh: {force_refresh}")
        return await health_service.get_domain_detail(domain_tag, time_range, force_refresh=force_refresh)
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


@router.get("/analysis/failures")
async def get_failure_analysis(
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for failure analysis"
    )
):
    """
    Get AI-powered failure analysis for all failed DAGs.
    
    Returns:
    - llm_analysis: AI-generated summary, categories, and action items
    - failed_dags: List of DAGs with failures
    - consolidated_logs: Logs from failed task instances
    - metadata: Total counts and timestamps
    """
    try:
        logger.info(f"GET /analysis/failures - time_range: {time_range.value}")
        return await health_service.get_failure_analysis(time_range)
    except Exception as e:
        import traceback
        logger.error(f"Error generating failure analysis: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate failure analysis: {str(e)}"
        )


@router.post("/slack/test")
async def test_slack_connection():
    """
    Test Slack webhook connection.
    
    Sends a test message to verify the Slack integration is configured correctly.
    """
    try:
        logger.info("POST /slack/test - Testing Slack connection")
        success = await slack_service.test_connection()
        
        if success:
            return {
                "status": "success",
                "message": "Slack connection test successful! Check your Slack channel for the test message."
            }
        else:
            return {
                "status": "failed",
                "message": "Slack connection test failed. Check webhook URL configuration."
            }
    except Exception as e:
        logger.error(f"Error testing Slack connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Slack test failed: {str(e)}")


@router.post("/reports/send")
async def send_report_now(
    time_range: TimeRange = Query(
        TimeRange.HOURS_24,
        description="Time range for the report"
    ),
    include_ai_analysis: bool = Query(
        True,
        description="Include AI-powered failure analysis in the report"
    )
):
    """
    Manually trigger a Slack report.
    
    This endpoint allows you to send an on-demand health report to Slack
    without waiting for the scheduled times.
    """
    try:
        logger.info(f"POST /reports/send - Sending manual report for {time_range.value}")
        
        success = await scheduled_reporter.generate_and_send_report(
            time_range=time_range,
            include_ai_analysis=include_ai_analysis
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Health report sent to Slack successfully!",
                "time_range": time_range.value,
                "ai_analysis_included": include_ai_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to send report to Slack. Check logs for details.",
                "time_range": time_range.value
            }
    
    except Exception as e:
        logger.error(f"Error sending manual report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send report: {str(e)}")


@router.get("/reports/schedule")
async def get_report_schedule():
    """
    Get current scheduled report configuration.
    
    Returns information about when reports are scheduled to be sent.
    """
    from app.config import settings
    
    return {
        "scheduled_reports_enabled": settings.scheduled_reports_enabled,
        "slack_enabled": settings.slack_enabled,
        "morning_report": {
            "time": f"{settings.morning_report_hour:02d}:{settings.morning_report_minute:02d}",
            "enabled": settings.scheduled_reports_enabled and settings.slack_enabled
        },
        "evening_report": {
            "time": f"{settings.evening_report_hour:02d}:{settings.evening_report_minute:02d}",
            "enabled": settings.scheduled_reports_enabled and settings.slack_enabled
        },
        "dashboard_url": settings.dashboard_url,
        "current_time": datetime.utcnow().strftime("%H:%M:%S"),
        "timezone": "UTC"
    }

