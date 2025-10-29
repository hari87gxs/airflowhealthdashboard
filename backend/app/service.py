"""
Health Service
Business logic for aggregating and calculating domain health.
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from loguru import logger

from app.models import (
    DomainHealthSummary,
    DagHealthSummary,
    DagRunSummary,
    DagRunState,
    TimeRange,
    DashboardResponse,
    DomainDetailResponse
)
from app.airflow_client import airflow_client
from app.cache import cache_service
from app.config import settings


class HealthService:
    """Service for calculating and aggregating DAG health metrics."""
    
    def __init__(self):
        self.airflow_client = airflow_client
        self.cache = cache_service
    
    async def get_dashboard_data(self, time_range: TimeRange = TimeRange.HOURS_24) -> DashboardResponse:
        """Get the main dashboard data with all domain summaries."""
        
        cache_key = f"dashboard:{time_range.value}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached dashboard data for {time_range.value}")
            return DashboardResponse(**cached_data)
        
        logger.info(f"Building dashboard data for time range: {time_range.value}")
        
        # Fetch all DAGs
        dags = await self.airflow_client.get_all_dags()
        
        # Group DAGs by tags
        dags_by_tag = self._group_dags_by_tags(dags)
        
        # Build domain summaries
        domain_summaries = []
        for tag, tag_dags in dags_by_tag.items():
            summary = await self._build_domain_summary(tag, tag_dags, time_range)
            domain_summaries.append(summary)
        
        # Sort: failures first, then by domain name
        domain_summaries.sort(key=lambda x: (not x.has_failures, x.domain_tag))
        
        response = DashboardResponse(
            time_range=time_range,
            domains=domain_summaries,
            total_domains=len(domain_summaries),
            total_dags=len(dags),
            last_updated=datetime.utcnow()
        )
        
        # Cache the response
        await self.cache.set(cache_key, response.model_dump())
        
        return response
    
    async def get_domain_detail(
        self, 
        domain_tag: str, 
        time_range: TimeRange = TimeRange.HOURS_24
    ) -> DomainDetailResponse:
        """Get detailed information for a specific domain."""
        
        cache_key = f"domain:{domain_tag}:{time_range.value}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached domain detail for {domain_tag}")
            return DomainDetailResponse(**cached_data)
        
        logger.info(f"Building domain detail for {domain_tag}, time range: {time_range.value}")
        
        # Fetch all DAGs and filter by tag
        all_dags = await self.airflow_client.get_all_dags()
        domain_dags = [
            dag for dag in all_dags 
            if domain_tag in dag.get("tags", [])
        ]
        
        if not domain_dags:
            raise ValueError(f"No DAGs found for domain tag: {domain_tag}")
        
        # Build detailed DAG summaries
        dag_summaries = []
        for dag in domain_dags:
            dag_summary = await self._build_dag_summary(dag, time_range)
            dag_summaries.append(dag_summary)
        
        # Sort: failures first, then by DAG ID
        dag_summaries.sort(key=lambda x: (x.failed_count == 0, x.dag_id))
        
        # Build domain summary
        domain_summary = await self._build_domain_summary(domain_tag, domain_dags, time_range)
        
        response = DomainDetailResponse(
            domain_tag=domain_tag,
            time_range=time_range,
            summary=domain_summary,
            dags=dag_summaries,
            last_updated=datetime.utcnow()
        )
        
        # Cache the response
        await self.cache.set(cache_key, response.model_dump())
        
        return response
    
    async def get_dag_runs(
        self, 
        dag_id: str, 
        time_range: TimeRange = TimeRange.HOURS_24,
        limit: int = 50
    ) -> List[DagRunSummary]:
        """Get recent runs for a specific DAG."""
        
        runs = await self.airflow_client.get_dag_runs(dag_id, time_range, limit)
        
        summaries = []
        for run in runs:
            summary = DagRunSummary(
                dag_id=dag_id,
                dag_run_id=run["dag_run_id"],
                execution_date=datetime.fromisoformat(run["execution_date"].replace("Z", "+00:00")),
                start_date=datetime.fromisoformat(run["start_date"].replace("Z", "+00:00")) if run.get("start_date") else None,
                end_date=datetime.fromisoformat(run["end_date"].replace("Z", "+00:00")) if run.get("end_date") else None,
                state=DagRunState(run["state"]),
                airflow_url=f"{settings.airflow_base_url}/dags/{dag_id}/grid?dag_run_id={run['dag_run_id']}"
            )
            summaries.append(summary)
        
        return summaries
    
    def _group_dags_by_tags(self, dags: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group DAGs by their tags."""
        
        dags_by_tag = defaultdict(list)
        
        for dag in dags:
            tags = dag.get("tags", [])
            
            if not tags:
                # DAGs without tags go into "untagged" group
                dags_by_tag["untagged"].append(dag)
            else:
                for tag in tags:
                    dags_by_tag[tag].append(dag)
        
        return dict(dags_by_tag)
    
    async def _build_domain_summary(
        self, 
        tag: str, 
        dags: List[Dict[str, Any]], 
        time_range: TimeRange
    ) -> DomainHealthSummary:
        """Build aggregated health summary for a domain."""
        
        total_failed = 0
        total_success = 0
        total_running = 0
        total_queued = 0
        total_runs = 0
        
        # Fetch runs for all DAGs in this domain
        dag_ids = [dag["dag_id"] for dag in dags]
        all_runs = await self.airflow_client.get_all_dag_runs_for_dags(dag_ids, time_range)
        
        for dag_id, runs in all_runs.items():
            for run in runs:
                state = run.get("state", "").lower()
                total_runs += 1
                
                if state == "failed":
                    total_failed += 1
                elif state == "success":
                    total_success += 1
                elif state == "running":
                    total_running += 1
                elif state == "queued":
                    total_queued += 1
        
        # Calculate health score
        if total_runs > 0:
            health_score = (total_success / total_runs) * 100
        else:
            health_score = 100.0
        
        return DomainHealthSummary(
            domain_tag=tag,
            total_dags=len(dags),
            total_runs=total_runs,
            failed_count=total_failed,
            success_count=total_success,
            running_count=total_running,
            queued_count=total_queued,
            has_failures=total_failed > 0,
            health_score=round(health_score, 2),
            last_updated=datetime.utcnow()
        )
    
    async def _build_dag_summary(
        self, 
        dag: Dict[str, Any], 
        time_range: TimeRange
    ) -> DagHealthSummary:
        """Build health summary for a single DAG."""
        
        dag_id = dag["dag_id"]
        runs = await self.airflow_client.get_dag_runs(dag_id, time_range)
        
        failed_count = 0
        success_count = 0
        running_count = 0
        queued_count = 0
        last_run_state = None
        last_run_date = None
        
        for i, run in enumerate(runs):
            state = run.get("state", "").lower()
            
            if i == 0:  # First run is the most recent
                last_run_state = DagRunState(state) if state in [s.value for s in DagRunState] else None
                exec_date = run.get("execution_date")
                if exec_date:
                    last_run_date = datetime.fromisoformat(exec_date.replace("Z", "+00:00"))
            
            if state == "failed":
                failed_count += 1
            elif state == "success":
                success_count += 1
            elif state == "running":
                running_count += 1
            elif state == "queued":
                queued_count += 1
        
        return DagHealthSummary(
            dag_id=dag_id,
            dag_display_name=dag.get("dag_display_name"),
            description=dag.get("description"),
            is_paused=dag.get("is_paused", False),
            tags=dag.get("tags", []),
            total_runs=len(runs),
            failed_count=failed_count,
            success_count=success_count,
            running_count=running_count,
            queued_count=queued_count,
            last_run_state=last_run_state,
            last_run_date=last_run_date,
            airflow_dag_url=f"{settings.airflow_base_url}/dags/{dag_id}/grid"
        )


# Global service instance
health_service = HealthService()
