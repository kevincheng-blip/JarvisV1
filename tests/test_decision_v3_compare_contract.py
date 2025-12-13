"""
Decision V3 Compare Contract Tests

Tests for Decision V3 compare endpoints (recompute, latest, list).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from jgod.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_compare_service():
    """Mock compare service functions"""
    with patch("jgod.api.routers.decision_v3.recompute_compare_and_save") as mock_recompute, \
         patch("jgod.api.routers.decision_v3.get_latest_compare") as mock_latest, \
         patch("jgod.api.routers.decision_v3.list_compare_snapshots") as mock_list:
        yield {
            "recompute": mock_recompute,
            "latest": mock_latest,
            "list": mock_list,
        }


def test_recompute_compare_contract(mock_compare_service):
    """Test POST /api/v1/decision-v3/compare/recompute/{symbol}"""
    # Mock successful recompute
    mock_snapshot = {
        "compare_id": "test-compare-123",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "mode": "performance",
        "limit": 60,
        "k": 5,
        "window": 20,
        "compare": {
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "winner": "V3",
            "delta_metrics": {
                "hit_rate_proxy": 0.05,
                "avg_return_proxy": 0.01,
                "max_drawdown_proxy": -0.03,
                "turnover_proxy": 0.02,
                "decision_consistency": 0.10,
            },
            "summary": "Decision V3 表現優於 Baseline。",
            "recommendation_next_step": "建議：維持 Decision V3 當前配置。",
        },
    }
    mock_compare_service["recompute"].return_value = mock_snapshot
    
    response = client.post(
        "/api/v1/decision-v3/compare/recompute/2330?mode=performance&limit=60&k=5&window=20"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "compare_id" in data
    assert data["symbol"] == "2330"
    assert data["mode"] == "performance"
    assert "compare" in data
    # CompareSnapshotResponseSchema structure: compare.compare.winner
    compare_inner = data["compare"]
    assert "compare" in compare_inner
    assert "winner" in compare_inner["compare"]
    assert compare_inner["compare"]["winner"] in ["V3", "BASELINE", "TIE", "NO_DATA"]


def test_get_latest_compare_contract(mock_compare_service):
    """Test GET /api/v1/decision-v3/compare/latest/{symbol}"""
    # Mock successful latest
    mock_snapshot = {
        "compare_id": "test-compare-123",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "mode": "performance",
        "limit": 60,
        "k": 5,
        "window": 20,
        "compare": {
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "winner": "V3",
            "delta_metrics": {
                "hit_rate_proxy": 0.05,
                "avg_return_proxy": 0.01,
                "max_drawdown_proxy": -0.03,
                "turnover_proxy": 0.02,
                "decision_consistency": 0.10,
            },
            "summary": "Decision V3 表現優於 Baseline。",
            "recommendation_next_step": "建議：維持 Decision V3 當前配置。",
        },
    }
    mock_compare_service["latest"].return_value = mock_snapshot
    
    response = client.get("/api/v1/decision-v3/compare/latest/2330")
    
    assert response.status_code == 200
    data = response.json()
    assert "compare_id" in data
    assert data["symbol"] == "2330"
    assert "compare" in data
    # CompareSnapshotResponseSchema structure: compare.compare.winner
    compare_inner = data["compare"]
    assert "compare" in compare_inner
    assert "winner" in compare_inner["compare"]


def test_get_latest_compare_no_data(mock_compare_service):
    """Test GET /api/v1/decision-v3/compare/latest/{symbol} with no data (still 200)"""
    # Mock no data
    mock_compare_service["latest"].return_value = None
    
    response = client.get("/api/v1/decision-v3/compare/latest/9999")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999"
    assert "compare" in data
    # CompareSnapshotResponseSchema structure: compare.compare.winner
    compare_inner = data["compare"]
    assert "compare" in compare_inner
    assert compare_inner["compare"]["winner"] == "NO_DATA"
    assert "暫無存檔的對照評估快照" in compare_inner["compare"]["summary"]


def test_list_compares_contract(mock_compare_service):
    """Test GET /api/v1/decision-v3/compare/list/{symbol}"""
    # Mock successful list
    mock_snapshots = [
        {
            "compare_id": "test-compare-1",
            "created_at": "2025-12-13T10:00:00",
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "compare": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "winner": "V3",
                "delta_metrics": {},
                "summary": "Decision V3 表現優於 Baseline。",
                "recommendation_next_step": "",
            },
        },
        {
            "compare_id": "test-compare-2",
            "created_at": "2025-12-12T10:00:00",
            "symbol": "2330",
            "mode": "performance",
            "limit": 60,
            "k": 5,
            "window": 20,
            "compare": {
                "symbol": "2330",
                "mode": "performance",
                "limit": 60,
                "k": 5,
                "window": 20,
                "winner": "BASELINE",
                "delta_metrics": {},
                "summary": "Baseline 表現優於 Decision V3。",
                "recommendation_next_step": "",
            },
        },
    ]
    mock_compare_service["list"].return_value = mock_snapshots
    
    response = client.get("/api/v1/decision-v3/compare/list/2330?n=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "2330"
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert "compare_id" in data["items"][0]
    assert isinstance(data["items"][0]["compare_id"], str)
    assert len(data["items"][0]["compare_id"]) > 0
    assert data["items"][0]["winner"] == "V3"


def test_list_compares_empty(mock_compare_service):
    """Test GET /api/v1/decision-v3/compare/list/{symbol} with empty list (still 200)"""
    # Mock empty list
    mock_compare_service["list"].return_value = []
    
    response = client.get("/api/v1/decision-v3/compare/list/9999?n=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999"
    assert "items" in data
    assert len(data["items"]) == 0
    assert data["total"] == 0

