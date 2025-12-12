"""
Strategy Performance Feed Contract Tests

Tests the API contract for strategy performance endpoints.
"""

from fastapi.testclient import TestClient
from jgod.api.main import app
from unittest.mock import patch
from datetime import date, timedelta

client = TestClient(app)


def test_recompute_200_and_schema():
    """Test recompute endpoint returns 200 with correct schema"""
    # Mock timeline data (enough points to avoid NO_DATA)
    mock_timeline = [
        {"date": (date.today() - timedelta(days=i)).isoformat(), "final_score": 10.0 + i * 0.1}
        for i in range(15)
    ]
    mock_timeline.reverse()  # Chronological order
    
    with patch("jgod.strategy_perf.service._fetch_timeline_from_db") as mock_fetch:
        mock_fetch.return_value = mock_timeline
        
        response = client.post("/api/v1/strategy-perf/recompute/2330?limit=60&window=20")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required fields
        assert "snapshot_id" in data
        assert "symbol" in data
        assert "items" in data
        assert "limit" in data
        assert "window" in data
        
        # Check items structure
        if data["items"]:  # If not empty
            item = data["items"][0]
            assert "strategy_id" in item
            assert "sharpe_proxy" in item
            assert "max_drawdown_proxy" in item
            assert "turnover_proxy" in item
            assert "decay_slope" in item
            assert "grade" in item


def test_recompute_and_latest():
    """Test recompute → latest can read the saved snapshot"""
    # Mock timeline data
    mock_timeline = [
        {"date": (date.today() - timedelta(days=i)).isoformat(), "final_score": 10.0 + i * 0.1}
        for i in range(15)
    ]
    mock_timeline.reverse()
    
    with patch("jgod.strategy_perf.service._fetch_timeline_from_db") as mock_fetch:
        mock_fetch.return_value = mock_timeline
        
        # Step 1: Recompute (save snapshot)
        recompute_response = client.post("/api/v1/strategy-perf/recompute/2330?limit=60&window=20")
        assert recompute_response.status_code == 200, f"Expected 200, got {recompute_response.status_code}: {recompute_response.text}"
        
        recompute_data = recompute_response.json()
        assert "snapshot_id" in recompute_data
        snapshot_id = recompute_data["snapshot_id"]
        
        # Step 2: Get latest (should return the saved snapshot)
        latest_response = client.get("/api/v1/strategy-perf/latest/2330")
        assert latest_response.status_code == 200, f"Expected 200, got {latest_response.status_code}: {latest_response.text}"
        
        latest_data = latest_response.json()
        assert latest_data["snapshot_id"] == snapshot_id, "Latest snapshot should match recomputed snapshot"
        assert latest_data["symbol"] == "2330"


def test_no_data_handling():
    """Test that no data still returns 200 with empty items"""
    # Mock empty timeline
    with patch("jgod.strategy_perf.service._fetch_timeline_from_db") as mock_fetch:
        mock_fetch.return_value = []
        
        # Latest endpoint (no saved snapshot)
        latest_response = client.get("/api/v1/strategy-perf/latest/NO_SYMBOL")
        assert latest_response.status_code == 200, f"Expected 200 even with no snapshot, got {latest_response.status_code}: {latest_response.text}"
        
        latest_data = latest_response.json()
        assert latest_data["items"] == []
        assert latest_data["symbol"] == "NO_SYMBOL"

