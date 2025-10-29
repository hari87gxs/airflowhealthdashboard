"""
Tests for the Airflow API Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.airflow_client import AirflowAPIClient
from app.models import TimeRange


@pytest.fixture
def airflow_client():
    """Fixture for AirflowAPIClient"""
    with patch('app.airflow_client.settings') as mock_settings:
        mock_settings.airflow_base_url = 'http://test-airflow:8080'
        mock_settings.airflow_username = 'test_user'
        mock_settings.airflow_password = 'test_pass'
        mock_settings.airflow_api_token = None
        client = AirflowAPIClient()
        return client


@pytest.mark.asyncio
async def test_get_all_dags(airflow_client):
    """Test fetching all DAGs"""
    mock_response = {
        'dags': [
            {'dag_id': 'test_dag_1', 'tags': ['Finance']},
            {'dag_id': 'test_dag_2', 'tags': ['Marketing']}
        ],
        'total_entries': 2
    }
    
    with patch.object(airflow_client, '_make_request', return_value=mock_response):
        dags = await airflow_client.get_all_dags()
        
        assert len(dags) == 2
        assert dags[0]['dag_id'] == 'test_dag_1'
        assert dags[1]['dag_id'] == 'test_dag_2'


@pytest.mark.asyncio
async def test_get_dag_runs(airflow_client):
    """Test fetching DAG runs"""
    mock_response = {
        'dag_runs': [
            {
                'dag_run_id': 'run_1',
                'state': 'success',
                'execution_date': '2025-10-29T09:00:00Z'
            }
        ]
    }
    
    with patch.object(airflow_client, '_make_request', return_value=mock_response):
        runs = await airflow_client.get_dag_runs('test_dag', TimeRange.HOURS_24)
        
        assert len(runs) == 1
        assert runs[0]['dag_run_id'] == 'run_1'
        assert runs[0]['state'] == 'success'


@pytest.mark.asyncio
async def test_test_connection_success(airflow_client):
    """Test successful connection test"""
    with patch.object(airflow_client, '_make_request', return_value={'status': 'healthy'}):
        result = await airflow_client.test_connection()
        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(airflow_client):
    """Test failed connection test"""
    with patch.object(airflow_client, '_make_request', side_effect=Exception('Connection failed')):
        result = await airflow_client.test_connection()
        assert result is False
