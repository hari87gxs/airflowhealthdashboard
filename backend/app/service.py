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
        fallback_cache_key = f"dashboard_fallback:{time_range.value}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached dashboard data for {time_range.value}")
            return DashboardResponse(**cached_data)
        
        logger.info(f"Building dashboard data for time range: {time_range.value}")
        
        try:
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
            
            # Cache the response with normal TTL
            await self.cache.set(cache_key, response.model_dump())
            
            # Also save as fallback with longer TTL (1 hour)
            await self.cache.set(fallback_cache_key, response.model_dump(), ttl=3600)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to fetch dashboard data from Airflow: {str(e)}")
            
            # Try to return fallback cached data
            fallback_data = await self.cache.get(fallback_cache_key)
            if fallback_data:
                logger.warning(f"Airflow unavailable, returning stale cached data for {time_range.value}")
                response = DashboardResponse(**fallback_data)
                # Mark as stale data
                logger.info("Using fallback cache due to Airflow unavailability")
                return response
            
            # No fallback available, re-raise the exception
            logger.error("No fallback cache available, failing request")
            raise
    
    async def get_domain_detail(
        self, 
        domain_tag: str, 
        time_range: TimeRange = TimeRange.HOURS_24
    ) -> DomainDetailResponse:
        """Get detailed information for a specific domain."""
        
        cache_key = f"domain:{domain_tag}:{time_range.value}"
        fallback_cache_key = f"domain_fallback:{domain_tag}:{time_range.value}"
        
        # Try cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached domain detail for {domain_tag}")
            return DomainDetailResponse(**cached_data)
        
        logger.info(f"Building domain detail for {domain_tag}, time range: {time_range.value}")
        
        try:
            # Fetch all DAGs and filter by domain tag
            all_dags = await self.airflow_client.get_all_dags()
            
            # Filter DAGs that have this domain tag
            domain_dags = []
            for dag in all_dags:
                tags = dag.get("tags", [])
                
                # Normalize tags to list of strings
                tag_names = []
                if isinstance(tags, list):
                    for tag in tags:
                        if isinstance(tag, str):
                            tag_names.append(tag)
                        elif isinstance(tag, dict) and 'name' in tag:
                            tag_names.append(tag['name'])
                
                # Check if this DAG has the domain tag
                domain_tag_to_find = f"domain:{domain_tag}"
                if domain_tag_to_find in tag_names:
                    domain_dags.append(dag)
            
            logger.info(f"Found {len(domain_dags)} DAGs for domain {domain_tag}")
            
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
            
            # Cache the response with normal TTL
            await self.cache.set(cache_key, response.model_dump())
            
            # Also save as fallback with longer TTL (1 hour)
            await self.cache.set(fallback_cache_key, response.model_dump(), ttl=3600)
            
            return response
            
        except ValueError as ve:
            # Domain not found - don't cache this
            raise ve
        except Exception as e:
            logger.error(f"Failed to fetch domain detail from Airflow: {str(e)}")
            
            # Try to return fallback cached data
            fallback_data = await self.cache.get(fallback_cache_key)
            if fallback_data:
                logger.warning(f"Airflow unavailable, returning stale cached data for domain {domain_tag}")
                return DomainDetailResponse(**fallback_data)
            
            # No fallback available, re-raise the exception
            logger.error("No fallback cache available, failing request")
            raise
    
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
        """Group DAGs by their domain tag. Looks for tags with 'domain:' prefix."""
        
        dags_by_domain = defaultdict(list)
        
        for dag in dags:
            tags = dag.get("tags", [])
            dag_id = dag.get("dag_id", "unknown")
            domain_found = False
            
            # Handle case where tags might not be a list (e.g., dict, None, etc.)
            if not tags:
                # DAGs without tags go into "untagged" group
                dags_by_domain["untagged"].append(dag)
                continue
            
            # Normalize tags to a list of strings
            tag_names = []
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str):
                        tag_names.append(tag)
                    elif isinstance(tag, dict) and 'name' in tag:
                        tag_names.append(tag['name'])
            elif isinstance(tags, dict):
                if 'name' in tags:
                    tag_names.append(tags['name'])
                else:
                    tag_names.extend([str(k) for k in tags.keys()])
            
            # Look for domain tag (format: "domain:xxx")
            for tag_name in tag_names:
                if isinstance(tag_name, str) and tag_name.startswith('domain:'):
                    # Extract domain name after "domain:" prefix
                    domain_name = tag_name.split(':', 1)[1].strip()
                    if domain_name:
                        dags_by_domain[domain_name].append(dag)
                        domain_found = True
                        break  # Use first domain tag found
            
            # If no domain tag found, put in "untagged"
            if not domain_found:
                dags_by_domain["untagged"].append(dag)
        
        logger.info(f"Grouped {len(dags)} DAGs into {len(dags_by_domain)} domains: {list(dags_by_domain.keys())}")
        return dict(dags_by_domain)
    
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
        
        # Normalize tags to list of strings
        raw_tags = dag.get("tags", [])
        tag_names = []
        if isinstance(raw_tags, list):
            for tag in raw_tags:
                if isinstance(tag, str):
                    tag_names.append(tag)
                elif isinstance(tag, dict) and 'name' in tag:
                    tag_names.append(tag['name'])
        
        return DagHealthSummary(
            dag_id=dag_id,
            dag_display_name=dag.get("dag_display_name"),
            description=dag.get("description"),
            is_paused=dag.get("is_paused", False),
            tags=tag_names,
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
