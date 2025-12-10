"""Tests for Rule Simulation API"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from jgod.api.main import app
from jgod.rule_sim.models import (
    RuleSimReport,
    RuleSimExperimentConfig,
    RuleSimStatusSummary,
    RuleSimStatus,
    RuleSimArmMetrics,
    RuleSimDeltaMetrics,
    RuleSimArm,
    RuleSetRef,
    RuleSimTargetType,
)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_report():
    """Mock RuleSimReport"""
    config = RuleSimExperimentConfig(
        experiment_id="api-test-001",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        target_ruleset=RuleSetRef(
            id="B01#S12",
            type=RuleSimTargetType.DOCTRINE_SECTION,
        ),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        universe=["2330", "2317"],
    )
    
    return RuleSimReport(
        experiment_id="api-test-001",
        config=config,
        status=RuleSimStatusSummary(
            status=RuleSimStatus.SUCCESS,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            finished_at=datetime(2024, 1, 1, 10, 5, 0),
        ),
        baseline_metrics=RuleSimArmMetrics(
            arm=RuleSimArm.BASELINE,
            sharpe=1.0,
            max_drawdown=0.1,
            total_return=0.2,
            win_rate=0.55,
        ),
        variant_metrics=RuleSimArmMetrics(
            arm=RuleSimArm.VARIANT,
            sharpe=1.1,
            max_drawdown=0.11,
            total_return=0.23,
            win_rate=0.56,
        ),
        deltas=RuleSimDeltaMetrics(
            sharpe_delta=0.1,
            max_drawdown_delta=0.01,
            total_return_delta=0.03,
        ),
        recommendation="APPROVE",
        created_at=datetime(2024, 1, 1, 10, 5, 0),
    )


class TestRuleSimAPI:
    """Tests for Rule Simulation API endpoints"""
    
    @patch("jgod.api.routers.rule_sim._engine")
    def test_post_run_experiment(self, mock_engine, client, mock_report):
        """Test POST /api/v1/rule-sim/run"""
        # Setup mock
        mock_engine.run_experiment.return_value = mock_report
        
        # Request body
        request_body = {
            "target_ruleset": {
                "id": "B01#S12",
                "type": "doctrine_section",
            },
            "baseline_version_id": "v1",
            "variant_version_id": "proposal-v1",
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "universe": ["2330", "2317"],
            "path_a_config_name": "path_a_tw_basic_v1",
        }
        
        # Make request
        response = client.post("/api/v1/rule-sim/run", json=request_body)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "experiment_id" in data
        assert "status" in data
        assert data["status"]["status"] == "SUCCESS"
        
        # Verify engine was called
        mock_engine.run_experiment.assert_called_once()
    
    @patch("jgod.api.routers.rule_sim._storage")
    def test_get_recent_experiments(self, mock_storage, client, mock_report):
        """Test GET /api/v1/rule-sim/experiments/recent"""
        # Create second report
        report2 = RuleSimReport(
            experiment_id="api-test-002",
            config=RuleSimExperimentConfig(
                experiment_id="api-test-002",
                created_at=datetime(2024, 1, 2, 10, 0, 0),
                target_ruleset=RuleSetRef(
                    id="B02#S05",
                    type=RuleSimTargetType.DOCTRINE_SECTION,
                ),
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
            ),
            status=RuleSimStatusSummary(status=RuleSimStatus.SUCCESS),
            baseline_metrics=RuleSimArmMetrics(
                arm=RuleSimArm.BASELINE,
                sharpe=0.9,
            ),
            variant_metrics=RuleSimArmMetrics(
                arm=RuleSimArm.VARIANT,
                sharpe=0.95,
            ),
            deltas=RuleSimDeltaMetrics(sharpe_delta=0.05),
            recommendation="CAUTION",
            created_at=datetime(2024, 1, 2, 10, 5, 0),
        )
        
        # Setup mock
        mock_storage.load_recent.return_value = [mock_report, report2]
        
        # Make request
        response = client.get("/api/v1/rule-sim/experiments/recent?limit=10")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check first item
        item = data[0]
        assert "experiment_id" in item
        assert "sharpe_delta" in item
        assert "recommendation" in item
        assert item["recommendation"] == "APPROVE" or item["recommendation"] == "CAUTION"
    
    @patch("jgod.api.routers.rule_sim._storage")
    def test_get_experiment_by_id_found(self, mock_storage, client, mock_report):
        """Test GET /api/v1/rule-sim/experiments/{experiment_id} when found"""
        # Setup mock
        mock_storage.load_by_id.return_value = mock_report
        
        # Make request
        response = client.get("/api/v1/rule-sim/experiments/api-test-001")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == "api-test-001"
        assert "baseline_metrics" in data
        assert "variant_metrics" in data
        assert "deltas" in data
        assert data["baseline_metrics"]["sharpe"] == 1.0
        assert data["variant_metrics"]["sharpe"] == 1.1
    
    @patch("jgod.api.routers.rule_sim._storage")
    def test_get_experiment_by_id_not_found(self, mock_storage, client):
        """Test GET /api/v1/rule-sim/experiments/{experiment_id} when not found"""
        # Setup mock
        mock_storage.load_by_id.return_value = None
        
        # Make request
        response = client.get("/api/v1/rule-sim/experiments/nonexistent")
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

