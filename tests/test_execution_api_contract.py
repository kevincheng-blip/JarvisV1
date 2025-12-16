"""
Execution API Contract Tests

Tests for Execution API endpoints (ledger latest, recompute, order simulate).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from jgod.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_execution_service():
    """Mock execution service functions"""
    with patch("jgod.api.routers.execution.get_latest_ledger") as mock_latest, \
         patch("jgod.api.routers.execution.recompute_ledger") as mock_recompute, \
         patch("jgod.api.routers.execution.simulate_order_from_latest_decision") as mock_simulate:
        yield {
            "latest": mock_latest,
            "recompute": mock_recompute,
            "simulate": mock_simulate,
        }


def test_get_ledger_latest_contract(mock_execution_service):
    """Test GET /api/v1/execution/ledger/latest/{symbol}"""
    # Mock successful response
    mock_snapshot = {
        "snapshot_id": "test-snapshot-123",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "ledger": {
            "symbol": "2330",
            "cash": 900_000.0,
            "position": {
                "qty": 1000,
                "avg_cost": 100.0,
                "market_value": 110_000.0,
                "unrealized_pnl": 10_000.0,
            },
            "realized_pnl": 5_000.0,
            "unrealized_pnl": 10_000.0,
            "nav": 1_010_000.0,
            "last_price": 110.0,
            "updated_at": "2025-12-13T10:00:00",
        },
        "is_default": False,
    }
    mock_execution_service["latest"].return_value = mock_snapshot
    
    response = client.get("/api/v1/execution/ledger/latest/2330")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "2330"
    assert "ledger" in data
    assert "snapshot_id" in data
    assert "is_default" in data
    assert data["ledger"]["cash"] == 900_000.0
    assert data["ledger"]["position"]["qty"] == 1000


def test_get_ledger_latest_no_data(mock_execution_service):
    """Test GET /api/v1/execution/ledger/latest/{symbol} with no data (default ledger)"""
    # Mock default ledger (no snapshot exists)
    mock_default = {
        "snapshot_id": "",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "ledger": {
            "symbol": "2330",
            "cash": 1_000_000.0,
            "position": {
                "qty": 0,
                "avg_cost": 0.0,
                "market_value": 0.0,
                "unrealized_pnl": 0.0,
            },
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "nav": 1_000_000.0,
            "last_price": 100.0,
            "updated_at": "2025-12-13T10:00:00",
        },
        "is_default": True,
    }
    mock_execution_service["latest"].return_value = mock_default
    
    response = client.get("/api/v1/execution/ledger/latest/2330")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True
    assert data["ledger"]["position"]["qty"] == 0


def test_post_ledger_recompute_contract(mock_execution_service):
    """Test POST /api/v1/execution/ledger/recompute/{symbol}"""
    # Mock successful recompute
    mock_snapshot = {
        "snapshot_id": "new-snapshot-456",
        "created_at": "2025-12-13T10:00:00",
        "symbol": "2330",
        "ledger": {
            "symbol": "2330",
            "cash": 1_000_000.0,
            "position": {
                "qty": 0,
                "avg_cost": 0.0,
                "market_value": 0.0,
                "unrealized_pnl": 0.0,
            },
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "nav": 1_000_000.0,
            "last_price": 100.0,
            "updated_at": "2025-12-13T10:00:00",
        },
        "is_default": False,
    }
    mock_execution_service["recompute"].return_value = mock_snapshot
    
    response = client.post("/api/v1/execution/ledger/recompute/2330?initial_cash=1000000.0")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "2330"
    assert data["snapshot_id"] == "new-snapshot-456"
    assert data["is_default"] is False
    assert data["ledger"]["cash"] == 1_000_000.0


def test_post_order_simulate_contract(mock_execution_service):
    """Test POST /api/v1/execution/order/simulate/{symbol}"""
    # Mock successful simulation
    mock_result = {
        "symbol": "2330",
        "ledger": {
            "symbol": "2330",
            "cash": 900_000.0,
            "position": {
                "qty": 1000,
                "avg_cost": 100.0,
                "market_value": 110_000.0,
                "unrealized_pnl": 10_000.0,
            },
            "realized_pnl": 0.0,
            "unrealized_pnl": 10_000.0,
            "nav": 1_010_000.0,
            "last_price": 110.0,
            "updated_at": "2025-12-13T10:00:00",
        },
        "decision_v3": {
            "selected_primary_strategy": "trend_follow",
            "risk_plan": {
                "position_scale": 0.80,
                "risk_state": "RISK_ON",
            },
            "confidence": 0.75,
        },
        "order_request": {
            "symbol": "2330",
            "side": "BUY",
            "qty": 500,
            "reason": "目標倉位比例 80.00%，當前 10.89%，買入 500 股以達到目標",
            "target_position_scale": 0.80,
            "current_position_scale": 0.1089,
        },
        "price": 110.0,
        "has_data": True,
    }
    mock_execution_service["simulate"].return_value = mock_result
    
    response = client.post("/api/v1/execution/order/simulate/2330?mode=performance&limit=60&k=5")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "2330"
    assert "ledger" in data
    assert "decision_v3" in data
    assert "order_request" in data
    assert data["order_request"]["side"] in ["BUY", "SELL", "HOLD"]
    assert data["has_data"] is True


def test_post_order_simulate_hold(mock_execution_service):
    """Test POST /api/v1/execution/order/simulate/{symbol} returning HOLD"""
    # Mock HOLD order (no data or insufficient difference)
    mock_result = {
        "symbol": "2330",
        "ledger": {
            "symbol": "2330",
            "cash": 1_000_000.0,
            "position": {
                "qty": 0,
                "avg_cost": 0.0,
                "market_value": 0.0,
                "unrealized_pnl": 0.0,
            },
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "nav": 1_000_000.0,
            "last_price": 100.0,
            "updated_at": "2025-12-13T10:00:00",
        },
        "decision_v3": {},
        "order_request": {
            "symbol": "2330",
            "side": "HOLD",
            "qty": 0,
            "reason": "資料不足，無法產生訂單",
            "target_position_scale": 0.0,
            "current_position_scale": 0.0,
        },
        "price": 100.0,
        "has_data": False,
    }
    mock_execution_service["simulate"].return_value = mock_result
    
    response = client.post("/api/v1/execution/order/simulate/2330")
    
    assert response.status_code == 200
    data = response.json()
    assert data["order_request"]["side"] == "HOLD"
    assert data["order_request"]["qty"] == 0
    assert data["has_data"] is False
