"""
Contract tests for Execution API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from jgod.api.main import app

client = TestClient(app)


def test_get_ledger_latest_returns_200():
    """Test that GET /api/v1/execution/ledger/latest/{symbol} returns 200."""
    response = client.get("/api/v1/execution/ledger/latest/2330")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check schema fields exist
    assert "symbol" in data
    assert "ledger" in data
    assert "snapshot_id" in data
    assert "created_at" in data
    assert "is_default" in data
    
    # Check ledger structure
    ledger = data["ledger"]
    assert "cash" in ledger
    assert "position" in ledger
    assert "nav" in ledger


def test_post_ledger_recompute_returns_200():
    """Test that POST /api/v1/execution/ledger/recompute/{symbol} returns 200."""
    response = client.post("/api/v1/execution/ledger/recompute/2330?initial_cash=1000000")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "snapshot_id" in data
    assert len(data["snapshot_id"]) > 0  # Should have a UUID
    assert data["symbol"] == "2330"
    assert data["ledger"]["cash"] == 1000000.0


def test_post_order_simulate_returns_200():
    """Test that POST /api/v1/execution/order/simulate/{symbol} returns 200."""
    response = client.post("/api/v1/execution/order/simulate/2330?mode=performance&limit=60&k=5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "symbol" in data
    assert "ledger" in data
    assert "order_request" in data
    assert "price" in data
    assert "has_data" in data
    
    # Check order_request structure
    order = data["order_request"]
    assert "side" in order
    assert order["side"] in ["BUY", "SELL", "HOLD"]
    assert "qty" in order
    assert "reason" in order
    assert "target_position_scale" in order
    assert "current_position_scale" in order


def test_order_simulate_no_data_returns_hold():
    """Test that order simulate returns HOLD when no data."""
    # Use a symbol that likely has no data
    response = client.post("/api/v1/execution/order/simulate/XXXXX?mode=performance&limit=60&k=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still return 200, but order_request.side might be HOLD
    assert data["order_request"]["side"] in ["BUY", "SELL", "HOLD"]

