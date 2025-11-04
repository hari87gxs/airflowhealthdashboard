"""
Airflow API Client
Handles all communication with the Airflow REST API.
"""

import asyncio
import httpx
import boto3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from app.config import settings
from app.models import TimeRange


class AirflowAPIClient:
    """Client for interacting with the Airflow REST API."""

    def __init__(self):
        self.base_url = settings.airflow_base_url
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.mwaa_session_cookie = None
        self.mwaa_host = None

        # Set up authentication
        if settings.airflow_api_token:
            # Use API token if provided
            self.auth_headers = {
                "Authorization": f"Bearer {settings.airflow_api_token}"
            }
            self.auth = None
            self.auth_type = "token"
        elif settings.airflow_username and settings.airflow_password:
            # Use basic auth if username and password are provided
            self.auth_headers = {}
            self.auth = httpx.BasicAuth(
                settings.airflow_username, settings.airflow_password
            )
            self.auth_type = "basic"
        elif settings.aws_region and settings.mwaa_environment_name:
            # Use MWAA authentication if AWS settings are provided
            self.auth_headers = {}
            self.auth = None
            self.auth_type = "mwaa"
            # Get MWAA session info during initialization
            self._init_mwaa_session()
        else:
            raise ValueError(
                "Authentication configuration missing. Provide either:\n"
                "- AIRFLOW_API_TOKEN, or\n"
                "- AIRFLOW_USERNAME and AIRFLOW_PASSWORD, or\n"
                "- AWS_REGION and MWAA_ENVIRONMENT_NAME"
            )

    def _init_mwaa_session(self):
        """Initialize MWAA session by getting web token."""
        try:
            session_info = self._get_mwaa_session_info(
                settings.aws_region, settings.mwaa_environment_name
            )
            if session_info:
                self.mwaa_host, self.mwaa_session_cookie = session_info
                logger.info(
                    f"Successfully authenticated with MWAA environment: {settings.mwaa_environment_name}"
                )
            else:
                raise ValueError("Failed to get MWAA session info")
        except Exception as e:
            logger.error(f"Failed to initialize MWAA session: {str(e)}")
            raise

    def _get_mwaa_session_info(
        self, region: str, env_name: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get MWAA session info by obtaining a web login token.

        Args:
            region: AWS region where MWAA is deployed
            env_name: MWAA environment name

        Returns:
            Tuple of (web_server_host_name, session_cookie) or None if failed
        """
        try:
            # Initialize MWAA client and request a web login token
            mwaa = boto3.client("mwaa", region_name=region)
            response = mwaa.create_web_login_token(Name=env_name)

            # Extract the web server hostname and login token
            web_server_host_name = response["WebServerHostname"]
            web_token = response["WebToken"]

            # Construct the URL needed for authentication
            login_url = f"https://{web_server_host_name}/aws_mwaa/login"
            login_payload = {"token": web_token}

            # Make a POST request to the MWAA login url using the login payload
            with httpx.Client(timeout=10.0) as client:
                response = client.post(login_url, data=login_payload)

            # Check if login was successful
            if response.status_code == 200:
                # Return the hostname and the session cookie
                return (web_server_host_name, response.cookies["session"])
            else:
                # Log an error
                logger.error(f"Failed to log in to MWAA: HTTP {response.status_code}")
                return None
        except httpx.RequestError as e:
            # Log any exceptions raised during the request to the MWAA login endpoint
            logger.error(f"Request failed during MWAA authentication: {str(e)}")
            return None
        except Exception as e:
            # Log any other unexpected exceptions
            logger.error(
                f"An unexpected error occurred during MWAA authentication: {str(e)}"
            )
            return None

    def _refresh_mwaa_session_if_needed(self):
        """Refresh MWAA session if using MWAA authentication."""
        if self.auth_type == "mwaa":
            self._init_mwaa_session()

    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Airflow API."""
        url = f"{self.base_url}/api/v1/{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare request headers and auth based on auth type
                headers = dict(self.auth_headers)
                auth = self.auth
                cookies = None

                if self.auth_type == "mwaa":
                    # Use MWAA session cookie for authentication
                    if not self.mwaa_session_cookie:
                        raise ValueError("MWAA session cookie not available")
                    cookies = {"session": self.mwaa_session_cookie}
                    # Override URL to use MWAA host
                    url = f"https://{self.mwaa_host}/api/v1/{endpoint}"

                response = await client.get(
                    url,
                    headers=headers,
                    auth=auth,
                    cookies=cookies,
                    params=params or {},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            # If MWAA auth fails with 401, try refreshing the session
            if self.auth_type == "mwaa" and e.response.status_code == 401:
                logger.warning("MWAA session expired, attempting to refresh...")
                self._refresh_mwaa_session_if_needed()
                # Retry the request once with new session
                return await self._make_request(endpoint, params)

            logger.error(
                f"HTTP error from Airflow API: {e.response.status_code} - {e.response.text}"
            )
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
                "dags", params={"limit": limit, "offset": offset}
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
        self, dag_id: str, time_range: TimeRange = TimeRange.HOURS_24, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch DAG runs for a specific DAG within a time range."""

        # Calculate start date based on time range (returns ISO 8601 string)
        start_date = self._get_start_date_for_range(time_range)

        logger.debug(f"Fetching DAG runs for {dag_id} since {start_date}")

        response = await self._make_request(
            f"dags/{dag_id}/dagRuns",
            params={
                "limit": limit,
                "start_date_gte": start_date,
                "order_by": "-execution_date",
            },
        )

        return response.get("dag_runs", [])

    async def get_all_dag_runs_for_dags(
        self, dag_ids: List[str], time_range: TimeRange = TimeRange.HOURS_24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch DAG runs for multiple DAGs efficiently."""

        results = {}

        # Use httpx to make concurrent requests
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            start_date = self._get_start_date_for_range(
                time_range
            )  # Calculate once outside loop
            for dag_id in dag_ids:
                # Prepare URL, headers, auth, and cookies based on auth type
                if self.auth_type == "mwaa":
                    url = f"https://{self.mwaa_host}/api/v1/dags/{dag_id}/dagRuns"
                    headers = dict(self.auth_headers)
                    auth = None
                    cookies = {"session": self.mwaa_session_cookie}
                else:
                    url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"
                    headers = self.auth_headers
                    auth = self.auth
                    cookies = None

                params = {
                    "limit": 100,
                    "start_date_gte": start_date,  # Use string directly
                    "order_by": "-execution_date",
                }

                tasks.append(
                    client.get(
                        url, headers=headers, auth=auth, cookies=cookies, params=params
                    )
                )

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for dag_id, response in zip(dag_ids, responses):
                if isinstance(response, Exception):
                    logger.warning(
                        f"Failed to fetch runs for {dag_id}: {str(response)}"
                    )
                    results[dag_id] = []
                else:
                    try:
                        data = response.json()
                        results[dag_id] = data.get("dag_runs", [])
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse response for {dag_id}: {str(e)}"
                        )
                        results[dag_id] = []

        return results

    def _get_start_date_for_range(self, time_range: TimeRange) -> str:
        """Calculate the start date based on the time range.

        Returns ISO 8601 formatted string with timezone (e.g., '2025-10-28T08:24:22+00:00')
        that Airflow API expects.
        """
        now = datetime.utcnow()

        if time_range == TimeRange.HOURS_24:
            start_date = now - timedelta(hours=24)
        elif time_range == TimeRange.DAYS_7:
            start_date = now - timedelta(days=7)
        elif time_range == TimeRange.DAYS_30:
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(hours=24)

        # Format as ISO 8601 with timezone (Airflow expects this format)
        # Return string in format: 2025-10-28T08:24:22+00:00
        return start_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    async def get_failed_task_logs(
        self, dag_id: str, dag_run_id: str, task_id: str, try_number: int = 1
    ) -> Optional[str]:
        """
        Fetch logs for a failed task instance.

        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier
            task_id: Task identifier
            try_number: Task attempt number (default: 1)

        Returns:
            Task logs as string, or None if not available
        """
        try:
            response = await self._make_request(
                f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
            )
            return response.get("content", "")
        except Exception as e:
            logger.warning(f"Failed to fetch logs for {dag_id}/{task_id}: {str(e)}")
            return None

    async def get_task_instances(
        self, dag_id: str, dag_run_id: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch all task instances for a DAG run.

        Args:
            dag_id: DAG identifier
            dag_run_id: DAG run identifier

        Returns:
            List of task instance details
        """
        try:
            response = await self._make_request(
                f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
            )
            return response.get("task_instances", [])
        except Exception as e:
            logger.error(
                f"Failed to fetch task instances for {dag_id}/{dag_run_id}: {str(e)}"
            )
            return []


# Global client instance
airflow_client = AirflowAPIClient()
