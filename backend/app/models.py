"""
Data models for the application.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DagRunState(str, Enum):
    """DAG run states as defined by Airflow."""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    QUEUED = "queued"


class TimeRange(str, Enum):
    """Supported time ranges for filtering."""
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"


class DagRunSummary(BaseModel):
    """Summary of a single DAG run."""
    dag_id: str
    dag_run_id: str
    execution_date: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    state: DagRunState
    airflow_url: str = Field(..., description="Direct link to DAG run in Airflow UI")


class DagHealthSummary(BaseModel):
    """Health summary for a single DAG."""
    dag_id: str
    dag_display_name: Optional[str] = None
    description: Optional[str] = None
    is_paused: bool
    tags: List[str]
    total_runs: int
    failed_count: int
    success_count: int
    running_count: int
    queued_count: int
    last_run_state: Optional[DagRunState] = None
    last_run_date: Optional[datetime] = None
    airflow_dag_url: str = Field(..., description="Link to DAG in Airflow UI")


class DomainHealthSummary(BaseModel):
    """Aggregated health summary for a business domain/tag."""
    domain_tag: str
    total_dags: int
    total_runs: int
    failed_count: int
    success_count: int
    running_count: int
    queued_count: int
    has_failures: bool = Field(..., description="True if any DAG has failures")
    health_score: float = Field(
        ..., 
        description="Success rate (0-100%) in the time range",
        ge=0.0,
        le=100.0
    )
    last_updated: datetime


class DomainDetailResponse(BaseModel):
    """Detailed response for a specific domain with DAG-level details."""
    domain_tag: str
    time_range: TimeRange
    summary: DomainHealthSummary
    dags: List[DagHealthSummary]
    last_updated: datetime


class DashboardResponse(BaseModel):
    """Main dashboard response with all domain summaries."""
    time_range: TimeRange
    domains: List[DomainHealthSummary]
    total_domains: int
    total_dags: int
    last_updated: datetime


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    airflow_connection: str
    cache_status: str
    timestamp: datetime
