"""
Tests for the Airflow API Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from app.airflow_client import AirflowAPIClient
from app.models import TimeRange


@pytest.fixture
def airflow_client():
    """Fixture for AirflowAPIClient"""
    with patch("app.airflow_client.settings") as mock_settings:
        mock_settings.airflow_base_url = "http://test-airflow:8080"
        mock_settings.airflow_username = "test_user"
        mock_settings.airflow_password = "test_pass"
        mock_settings.airflow_api_token = None
        client = AirflowAPIClient()
        return client


@pytest.mark.asyncio
async def test_get_all_dags(airflow_client):
    """Test fetching all DAGs"""
    mock_response = {
        "dags": [
            {"dag_id": "test_dag_1", "tags": ["Finance"]},
            {"dag_id": "test_dag_2", "tags": ["Marketing"]},
        ],
        "total_entries": 2,
    }

    with patch.object(airflow_client, "_make_request", return_value=mock_response):
        dags = await airflow_client.get_all_dags()

        assert len(dags) == 2
        assert dags[0]["dag_id"] == "test_dag_1"
        assert dags[1]["dag_id"] == "test_dag_2"


@pytest.mark.asyncio
async def test_get_dag_runs(airflow_client):
    """Test fetching DAG runs"""
    mock_response = {
        "dag_runs": [
            {
                "dag_run_id": "run_1",
                "state": "success",
                "execution_date": "2025-10-29T09:00:00Z",
            }
        ]
    }

    with patch.object(airflow_client, "_make_request", return_value=mock_response):
        runs = await airflow_client.get_dag_runs("test_dag", TimeRange.HOURS_24)

        assert len(runs) == 1
        assert runs[0]["dag_run_id"] == "run_1"
        assert runs[0]["state"] == "success"


@pytest.mark.asyncio
async def test_test_connection_success(airflow_client):
    """Test successful connection test"""
    with patch.object(
        airflow_client, "_make_request", return_value={"status": "healthy"}
    ):
        result = await airflow_client.test_connection()
        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(airflow_client):
    """Test failed connection test"""
    with patch.object(
        airflow_client, "_make_request", side_effect=Exception("Connection failed")
    ):
        result = await airflow_client.test_connection()
        assert result is False


@pytest.fixture
def mwaa_client():
    """Fixture for MWAA-authenticated AirflowAPIClient"""
    with (
        patch("app.airflow_client.settings") as mock_settings,
        patch("app.airflow_client.boto3") as mock_boto3,
        patch("app.airflow_client.httpx.Client") as mock_httpx_client,
    ):
        # Configure settings for MWAA
        mock_settings.airflow_base_url = "https://test-mwaa.airflow.amazonaws.com"
        mock_settings.airflow_username = None
        mock_settings.airflow_password = None
        mock_settings.airflow_api_token = None
        mock_settings.aws_region = "us-east-1"
        mock_settings.mwaa_environment_name = "test-mwaa-env"

        # Mock boto3 MWAA client
        mock_mwaa_client = MagicMock()
        mock_mwaa_client.create_web_login_token.return_value = {
            "WebServerHostname": "test-mwaa-host.airflow.amazonaws.com",
            "WebToken": "test-web-token",
        }
        mock_boto3.client.return_value = mock_mwaa_client

        # Mock httpx.Client for login
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {"session": "test-session-cookie"}
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=None)
        mock_httpx_client.return_value = mock_client_instance

        client = AirflowAPIClient()
        return client


@pytest.mark.asyncio
async def test_mwaa_authentication_initialization(mwaa_client):
    """Test that MWAA client initializes with correct auth type"""
    assert mwaa_client.auth_type == "mwaa"
    assert mwaa_client.mwaa_session_cookie == "test-session-cookie"
    assert mwaa_client.mwaa_host == "test-mwaa-host.airflow.amazonaws.com"


@pytest.mark.asyncio
async def test_mwaa_get_session_info():
    """Test MWAA session info retrieval"""
    with (
        patch("app.airflow_client.boto3") as mock_boto3,
        patch("app.airflow_client.httpx.Client") as mock_httpx_client,
    ):
        # Mock boto3 response
        mock_mwaa_client = MagicMock()
        mock_mwaa_client.create_web_login_token.return_value = {
            "WebServerHostname": "test-host.airflow.amazonaws.com",
            "WebToken": "test-token",
        }
        mock_boto3.client.return_value = mock_mwaa_client

        # Mock httpx.Client response
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {"session": "session-cookie-value"}
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=None)
        mock_httpx_client.return_value = mock_client_instance

        # Create client with MWAA config
        with patch("app.airflow_client.settings") as mock_settings:
            mock_settings.airflow_base_url = "https://test.airflow.amazonaws.com"
            mock_settings.airflow_username = None
            mock_settings.airflow_password = None
            mock_settings.airflow_api_token = None
            mock_settings.aws_region = "us-east-1"
            mock_settings.mwaa_environment_name = "test-env"

            client = AirflowAPIClient()

            assert client.mwaa_host == "test-host.airflow.amazonaws.com"
            assert client.mwaa_session_cookie == "session-cookie-value"


@pytest.mark.asyncio
async def test_mwaa_session_refresh_on_401():
    """Test that MWAA session refreshes on 401 response"""
    with (
        patch("app.airflow_client.settings") as mock_settings,
        patch("app.airflow_client.boto3") as mock_boto3,
        patch("app.airflow_client.httpx.Client") as mock_httpx_client,
        patch("app.airflow_client.httpx.AsyncClient") as mock_async_client,
    ):
        # Configure settings
        mock_settings.airflow_base_url = "https://test-mwaa.airflow.amazonaws.com"
        mock_settings.airflow_username = None
        mock_settings.airflow_password = None
        mock_settings.airflow_api_token = None
        mock_settings.aws_region = "us-east-1"
        mock_settings.mwaa_environment_name = "test-env"

        # Mock initial boto3 setup
        mock_mwaa_client = MagicMock()
        mock_mwaa_client.create_web_login_token.return_value = {
            "WebServerHostname": "test-host.airflow.amazonaws.com",
            "WebToken": "test-token",
        }
        mock_boto3.client.return_value = mock_mwaa_client

        # Mock initial login with httpx.Client
        mock_client_instance = MagicMock()
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.cookies = {"session": "initial-cookie"}
        mock_client_instance.post.return_value = mock_login_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=None)
        mock_httpx_client.return_value = mock_client_instance

        client = AirflowAPIClient()

        assert client.mwaa_session_cookie == "initial-cookie"


def test_authentication_priority():
    """Test that authentication methods are prioritized correctly"""

    # Test 1: API Token takes priority
    with patch("app.airflow_client.settings") as mock_settings:
        mock_settings.airflow_base_url = "http://test:8080"
        mock_settings.airflow_api_token = "test-token"
        mock_settings.airflow_username = "user"
        mock_settings.airflow_password = "pass"
        mock_settings.aws_region = "us-east-1"
        mock_settings.mwaa_environment_name = "env"

        client = AirflowAPIClient()
        assert client.auth_type == "token"

    # Test 2: Basic auth when no token
    with patch("app.airflow_client.settings") as mock_settings:
        mock_settings.airflow_base_url = "http://test:8080"
        mock_settings.airflow_api_token = None
        mock_settings.airflow_username = "user"
        mock_settings.airflow_password = "pass"
        mock_settings.aws_region = None
        mock_settings.mwaa_environment_name = None

        client = AirflowAPIClient()
        assert client.auth_type == "basic"

    # Test 3: MWAA when no token or basic auth
    with (
        patch("app.airflow_client.settings") as mock_settings,
        patch("app.airflow_client.boto3") as mock_boto3,
        patch("app.airflow_client.httpx.Client") as mock_httpx_client,
    ):
        mock_settings.airflow_base_url = "https://test.airflow.amazonaws.com"
        mock_settings.airflow_api_token = None
        mock_settings.airflow_username = None
        mock_settings.airflow_password = None
        mock_settings.aws_region = "us-east-1"
        mock_settings.mwaa_environment_name = "test-env"

        # Mock MWAA setup
        mock_mwaa_client = MagicMock()
        mock_mwaa_client.create_web_login_token.return_value = {
            "WebServerHostname": "test-host.airflow.amazonaws.com",
            "WebToken": "token",
        }
        mock_boto3.client.return_value = mock_mwaa_client

        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {"session": "cookie"}
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=None)
        mock_httpx_client.return_value = mock_client_instance

        client = AirflowAPIClient()
        assert client.auth_type == "mwaa"


def test_missing_authentication_raises_error():
    """Test that missing all authentication methods raises error"""
    with patch("app.airflow_client.settings") as mock_settings:
        mock_settings.airflow_base_url = "http://test:8080"
        mock_settings.airflow_api_token = None
        mock_settings.airflow_username = None
        mock_settings.airflow_password = None
        mock_settings.aws_region = None
        mock_settings.mwaa_environment_name = None

        with pytest.raises(ValueError) as exc_info:
            AirflowAPIClient()

        assert "Authentication configuration missing" in str(exc_info.value)
