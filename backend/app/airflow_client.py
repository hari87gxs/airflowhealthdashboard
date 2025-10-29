"""
Airflow API Client
Handles all communication with the Airflow REST API.
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from app.config import settings
from app.models import TimeRange


class AirflowAPIClient:
    """Client for interacting with the Airflow REST API."""
    
    def __init__(self):
        self.base_url = settings.airflow_base_url
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Set up authentication
        if settings.airflow_api_token:
            self.auth_headers = {
                "Authorization": f"Bearer {settings.airflow_api_token}"
            }
            self.auth = None
        else:
            self.auth_headers = {}
            self.auth = httpx.BasicAuth(
                settings.airflow_username, 
                settings.airflow_password
            )
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Airflow API."""
        url = f"{self.base_url}/api/v1/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self.auth_headers,
                    auth=self.auth,
                    params=params or {}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Airflow API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to Airflow API: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test the connection to Airflow API."""
        try:
            await self._make_request("health")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Airflow: {str(e)}")
            return False
    
    async def get_all_dags(self) -> List[Dict[str, Any]]:
        """Fetch all DAGs from Airflow."""
        logger.info("Fetching all DAGs from Airflow API")
        
        all_dags = []
        offset = 0
        limit = 100
        
        while True:
            response = await self._make_request(
                "dags",
                params={"limit": limit, "offset": offset}
            )
            
            dags = response.get("dags", [])
            all_dags.extend(dags)
            
            total_entries = response.get("total_entries", 0)
            offset += limit
            
            if offset >= total_entries:
                break
        
        logger.info(f"Fetched {len(all_dags)} DAGs from Airflow")
        return all_dags
    
    async def get_dag_runs(
        self, 
        dag_id: str, 
        time_range: TimeRange = TimeRange.HOURS_24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch DAG runs for a specific DAG within a time range."""
        
        # Calculate start date based on time range
        start_date = self._get_start_date_for_range(time_range)
        
        logger.debug(f"Fetching DAG runs for {dag_id} since {start_date}")
        
        response = await self._make_request(
            f"dags/{dag_id}/dagRuns",
            params={
                "limit": limit,
                "start_date_gte": start_date.isoformat(),
                "order_by": "-execution_date"
            }
        )
        
        return response.get("dag_runs", [])
    
    async def get_all_dag_runs_for_dags(
        self, 
        dag_ids: List[str],
        time_range: TimeRange = TimeRange.HOURS_24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch DAG runs for multiple DAGs efficiently."""
        
        results = {}
        
        # Use httpx to make concurrent requests
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for dag_id in dag_ids:
                start_date = self._get_start_date_for_range(time_range)
                url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"
                params = {
                    "limit": 100,
                    "start_date_gte": start_date.isoformat(),
                    "order_by": "-execution_date"
                }
                
                tasks.append(
                    client.get(
                        url,
                        headers=self.auth_headers,
                        auth=self.auth,
                        params=params
                    )
                )
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for dag_id, response in zip(dag_ids, responses):
                if isinstance(response, Exception):
                    logger.warning(f"Failed to fetch runs for {dag_id}: {str(response)}")
                    results[dag_id] = []
                else:
                    try:
                        data = response.json()
                        results[dag_id] = data.get("dag_runs", [])
                    except Exception as e:
                        logger.warning(f"Failed to parse response for {dag_id}: {str(e)}")
                        results[dag_id] = []
        
        return results
    
    def _get_start_date_for_range(self, time_range: TimeRange) -> datetime:
        """Calculate the start date based on the time range."""
        now = datetime.utcnow()
        
        if time_range == TimeRange.HOURS_24:
            return now - timedelta(hours=24)
        elif time_range == TimeRange.DAYS_7:
            return now - timedelta(days=7)
        elif time_range == TimeRange.DAYS_30:
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)


# Global client instance
import asyncio
airflow_client = AirflowAPIClient()
