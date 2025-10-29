"""
Tests for the Health Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.service import HealthService
from app.models import TimeRange


@pytest.fixture
def health_service():
    """Fixture for HealthService"""
    return HealthService()


@pytest.mark.asyncio
async def test_get_dashboard_data(health_service):
    """Test getting dashboard data"""
    # Mock DAGs
    mock_dags = [
        {'dag_id': 'finance_dag_1', 'tags': ['Finance'], 'is_paused': False},
        {'dag_id': 'finance_dag_2', 'tags': ['Finance'], 'is_paused': False},
        {'dag_id': 'marketing_dag_1', 'tags': ['Marketing'], 'is_paused': False}
    ]
    
    # Mock DAG runs
    mock_runs = {
        'finance_dag_1': [
            {'state': 'success', 'execution_date': '2025-10-29T09:00:00Z'},
            {'state': 'failed', 'execution_date': '2025-10-29T08:00:00Z'}
        ],
        'finance_dag_2': [
            {'state': 'success', 'execution_date': '2025-10-29T09:00:00Z'}
        ],
        'marketing_dag_1': [
            {'state': 'success', 'execution_date': '2025-10-29T09:00:00Z'}
        ]
    }
    
    with patch.object(health_service.airflow_client, 'get_all_dags', return_value=mock_dags):
        with patch.object(health_service.airflow_client, 'get_all_dag_runs_for_dags', return_value=mock_runs):
            with patch.object(health_service.cache, 'get', return_value=None):
                with patch.object(health_service.cache, 'set', return_value=True):
                    result = await health_service.get_dashboard_data(TimeRange.HOURS_24)
                    
                    assert result.total_domains == 2
                    assert result.total_dags == 3
                    assert len(result.domains) == 2
                    
                    # Check Finance domain
                    finance = next(d for d in result.domains if d.domain_tag == 'Finance')
                    assert finance.total_dags == 2
                    assert finance.failed_count == 1
                    assert finance.success_count == 2


@pytest.mark.asyncio
async def test_get_domain_detail(health_service):
    """Test getting domain detail"""
    mock_dags = [
        {'dag_id': 'finance_dag_1', 'tags': ['Finance'], 'is_paused': False, 'description': 'Test DAG'}
    ]
    
    mock_runs = [
        {'state': 'success', 'execution_date': '2025-10-29T09:00:00Z', 'dag_run_id': 'run_1'}
    ]
    
    with patch.object(health_service.airflow_client, 'get_all_dags', return_value=mock_dags):
        with patch.object(health_service.airflow_client, 'get_dag_runs', return_value=mock_runs):
            with patch.object(health_service.airflow_client, 'get_all_dag_runs_for_dags', return_value={'finance_dag_1': mock_runs}):
                with patch.object(health_service.cache, 'get', return_value=None):
                    with patch.object(health_service.cache, 'set', return_value=True):
                        result = await health_service.get_domain_detail('Finance', TimeRange.HOURS_24)
                        
                        assert result.domain_tag == 'Finance'
                        assert len(result.dags) == 1
                        assert result.dags[0].dag_id == 'finance_dag_1'
                        assert result.summary.total_dags == 1
