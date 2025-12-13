"""
Decision V3 Evaluation Contract Tests

Tests for Decision V3 evaluation endpoints (recompute, latest, list).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from jgod.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_evaluation_service():
    """Mock evaluation service functions"""
    with patch("jgod.api.routers.decision_v3.recompute_evaluation_and_save") as mock_recompute, \
         patch("jgod.api.routers.decision_v3.get_latest_evaluation") as mock_latest, \
         patch("jgod.api.routers.decision_v3.list_evaluation_snapshots") as mock_list:
        yield {
            "recompute": mock_recompute,
            "latest": mock_latest,
            "list": mock_list,
        }


def test_recompute_evaluation_contract(mock_evaluation_service):
    """Test POST /api/v1/decision-v3/eval/recompute/{symbol}"""
    # Mock successful recompute
    mock_snapshot = {
        "eval_id": "test-eval-123",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "mode": "performance",
        "limit": 60,
        "k": 5,
        "window": 20,
        "evaluation": {
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "decision": {
                "primary_strategy": "trend_follow",
                "risk_plan": {
                    "position_scale": 0.80,
                    "risk_state": "RISK_ON",
                },
                "confidence": 0.75,
            },
            "inputs_summary": {
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "stability_grade": "STABLE",
                "perf_grade": "GOOD",
            },
            "metrics": {
                "n_points": 45,
                "hit_rate_proxy": 0.58,
                "avg_return_proxy": 0.012,
                "max_drawdown_proxy": 0.15,
                "turnover_proxy": 0.08,
                "decision_consistency": 0.75,
                "verdict": "IMPROVED",
                "recommendation_next_step": "決策表現良好，建議維持當前策略配置。",
            },
        },
    }
    mock_evaluation_service["recompute"].return_value = mock_snapshot
    
    response = client.post(
        "/api/v1/decision-v3/eval/recompute/2330?mode=performance&limit=60&k=5&window=20"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "eval_id" in data
    assert data["symbol"] == "2330"
    assert data["mode"] == "performance"
    assert "evaluation" in data
    assert "metrics" in data["evaluation"]
    assert data["evaluation"]["metrics"]["verdict"] in ["IMPROVED", "NEUTRAL", "REGRESSED", "NO_DATA"]


def test_get_latest_evaluation_contract(mock_evaluation_service):
    """Test GET /api/v1/decision-v3/eval/latest/{symbol}"""
    # Mock successful latest
    mock_snapshot = {
        "eval_id": "test-eval-123",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "mode": "performance",
        "limit": 60,
        "k": 5,
        "window": 20,
        "evaluation": {
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "decision": {
                "primary_strategy": "trend_follow",
                "risk_plan": {
                    "position_scale": 0.80,
                    "risk_state": "RISK_ON",
                },
                "confidence": 0.75,
            },
            "inputs_summary": {
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "stability_grade": "STABLE",
                "perf_grade": "GOOD",
            },
            "metrics": {
                "n_points": 45,
                "hit_rate_proxy": 0.58,
                "avg_return_proxy": 0.012,
                "max_drawdown_proxy": 0.15,
                "turnover_proxy": 0.08,
                "decision_consistency": 0.75,
                "verdict": "IMPROVED",
                "recommendation_next_step": "決策表現良好，建議維持當前策略配置。",
            },
        },
    }
    mock_evaluation_service["latest"].return_value = mock_snapshot
    
    response = client.get("/api/v1/decision-v3/eval/latest/2330")
    
    assert response.status_code == 200
    data = response.json()
    assert "eval_id" in data
    assert data["symbol"] == "2330"
    assert "evaluation" in data
    assert "metrics" in data["evaluation"]


def test_get_latest_evaluation_no_data(mock_evaluation_service):
    """Test GET /api/v1/decision-v3/eval/latest/{symbol} with no data (still 200)"""
    # Mock no data
    mock_evaluation_service["latest"].return_value = None
    
    response = client.get("/api/v1/decision-v3/eval/latest/9999")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999"
    assert "evaluation" in data
    assert data["evaluation"]["metrics"]["verdict"] == "NO_DATA"
    assert "暫無存檔的評估快照" in data["evaluation"]["metrics"]["recommendation_next_step"]


def test_list_evaluations_contract(mock_evaluation_service):
    """Test GET /api/v1/decision-v3/eval/list/{symbol}"""
    # Mock successful list
    mock_snapshots = [
        {
            "eval_id": "test-eval-1",
            "created_at": "2025-12-13T10:00:00",
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "evaluation": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "decision": {},
                "inputs_summary": {},
                "metrics": {
                    "verdict": "IMPROVED",
                    "hit_rate_proxy": 0.58,
                    "avg_return_proxy": 0.012,
                    "max_drawdown_proxy": 0.15,
                },
            },
        },
        {
            "eval_id": "test-eval-2",
            "created_at": "2025-12-12T10:00:00",
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "evaluation": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "decision": {},
                "inputs_summary": {},
                "metrics": {
                    "verdict": "NEUTRAL",
                    "hit_rate_proxy": 0.50,
                    "avg_return_proxy": 0.005,
                    "max_drawdown_proxy": 0.20,
                },
            },
        },
    ]
    mock_evaluation_service["list"].return_value = mock_snapshots
    
    response = client.get("/api/v1/decision-v3/eval/list/2330?n=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "2330"
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert "eval_id" in data["items"][0]
    assert isinstance(data["items"][0]["eval_id"], str)
    assert len(data["items"][0]["eval_id"]) > 0
    assert data["items"][0]["verdict"] == "IMPROVED"


def test_list_evaluations_empty(mock_evaluation_service):
    """Test GET /api/v1/decision-v3/eval/list/{symbol} with empty list (still 200)"""
    # Mock empty list
    mock_evaluation_service["list"].return_value = []
    
    response = client.get("/api/v1/decision-v3/eval/list/9999?n=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999"
    assert "items" in data
    assert len(data["items"]) == 0
    assert data["total"] == 0

