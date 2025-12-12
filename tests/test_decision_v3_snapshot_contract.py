"""
Decision V3 Snapshot Contract Tests

Tests the API contract for Decision V3 snapshot endpoints.
"""

from fastapi.testclient import TestClient
from jgod.api.main import app
from unittest.mock import patch, MagicMock
from datetime import datetime

client = TestClient(app)


def test_recompute_200_and_schema():
    """Test recompute endpoint returns 200 with correct schema and snapshot_id"""
    # Mock compute_decision to return a valid result
    mock_result = MagicMock()
    mock_result.symbol = "2330"
    mock_result.as_of_date = None
    mock_result.selected_primary_strategy = "trend_follow"
    mock_result.selected_secondary_strategies = ["momentum"]
    mock_result.weights = [
        MagicMock(strategy_id="trend_follow", weight=0.52, grade=None, metrics=None, rationale="test"),
    ]
    mock_result.risk_plan = MagicMock()
    mock_result.risk_plan.position_scale = 0.80
    mock_result.risk_plan.risk_state = "RISK_ON"
    mock_result.risk_plan.reasons = ["預測穩定性為 STABLE"]
    mock_result.confidence = 0.85
    mock_result.explain = "測試說明"
    
    with patch("jgod.decision_v3.service.compute_decision") as mock_compute, \
         patch("jgod.decision_v3.storage.save_snapshot") as mock_save:
        mock_compute.return_value = mock_result
        
        # Mock save_snapshot to add snapshot_id to the snapshot dict and return it
        def mock_save_side_effect(snapshot):
            snapshot["snapshot_id"] = "test-snapshot-id-123"
            return "test-snapshot-id-123"
        
        mock_save.side_effect = mock_save_side_effect
        
        response = client.post("/api/v1/decision-v3/recompute/2330?mode=performance&limit=60&k=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required fields
        assert "snapshot_id" in data
        assert len(data["snapshot_id"]) > 0, "snapshot_id should not be empty"
        assert "created_at" in data
        assert "symbol" in data
        assert "mode" in data
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "selected_primary_strategy" in result
        assert "risk_plan" in result
        assert "confidence" in result
        assert "explain" in result


def test_recompute_and_latest():
    """Test recompute → latest can read the saved snapshot"""
    # Mock compute_decision
    mock_result = MagicMock()
    mock_result.symbol = "2330"
    mock_result.as_of_date = None
    mock_result.selected_primary_strategy = "trend_follow"
    mock_result.selected_secondary_strategies = []
    mock_result.weights = []
    mock_result.risk_plan = MagicMock()
    mock_result.risk_plan.position_scale = 0.80
    mock_result.risk_plan.risk_state = "RISK_ON"
    mock_result.risk_plan.reasons = []
    mock_result.confidence = 0.85
    mock_result.explain = "測試"
    
    saved_snapshot = None
    
    def mock_save(snapshot):
        nonlocal saved_snapshot
        saved_snapshot = snapshot
        return snapshot.get("snapshot_id", "test-id")
    
    with patch("jgod.decision_v3.service.compute_decision") as mock_compute, \
         patch("jgod.decision_v3.storage.save_snapshot", side_effect=mock_save), \
         patch("jgod.decision_v3.storage.load_latest") as mock_load:
        mock_compute.return_value = mock_result
        
        # Step 1: Recompute (save snapshot)
        recompute_response = client.post("/api/v1/decision-v3/recompute/2330?mode=performance")
        assert recompute_response.status_code == 200, f"Expected 200, got {recompute_response.status_code}: {recompute_response.text}"
        
        recompute_data = recompute_response.json()
        assert "snapshot_id" in recompute_data
        snapshot_id = recompute_data["snapshot_id"]
        
        # Step 2: Mock load_latest to return the saved snapshot
        if saved_snapshot:
            saved_snapshot["snapshot_id"] = snapshot_id
            mock_load.return_value = saved_snapshot
        
        # Step 3: Get latest (should return the saved snapshot)
        latest_response = client.get("/api/v1/decision-v3/latest/2330")
        assert latest_response.status_code == 200, f"Expected 200, got {latest_response.status_code}: {latest_response.text}"
        
        latest_data = latest_response.json()
        assert latest_data["snapshot_id"] == snapshot_id, "Latest snapshot should match recomputed snapshot"
        assert latest_data["symbol"] == "2330"


def test_list_snapshots():
    """Test list endpoint returns 200 with items list"""
    # Mock list_snapshots
    mock_snapshots = [
        {
            "snapshot_id": "id-1",
            "created_at": datetime.now(),
            "symbol": "2330",
            "mode": "performance",
            "result": {
                "selected_primary_strategy": "trend_follow",
                "confidence": 0.85,
                "risk_plan": {"risk_state": "RISK_ON"},
            },
        },
        {
            "snapshot_id": "id-2",
            "created_at": datetime.now(),
            "symbol": "2330",
            "mode": "performance",
            "result": {
                "selected_primary_strategy": "momentum",
                "confidence": 0.75,
                "risk_plan": {"risk_state": "CAUTION"},
            },
        },
    ]
    
    with patch("jgod.decision_v3.service.list_snapshots") as mock_list:
        mock_list.return_value = mock_snapshots
        
        response = client.get("/api/v1/decision-v3/list/2330?n=20")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "symbol" in data
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
        assert data["total"] >= 1


def test_no_data_handling():
    """Test that no data still returns 200 with RISK_OFF"""
    # Mock get_latest_snapshot to return None
    with patch("jgod.decision_v3.service.get_latest_snapshot") as mock_get:
        mock_get.return_value = None
        
        # Latest endpoint (no saved snapshot)
        latest_response = client.get("/api/v1/decision-v3/latest/NO_SYMBOL")
        assert latest_response.status_code == 200, f"Expected 200 even with no snapshot, got {latest_response.status_code}: {latest_response.text}"
        
        latest_data = latest_response.json()
        assert latest_data["result"]["risk_plan"]["risk_state"] == "RISK_OFF"
        assert latest_data["result"]["risk_plan"]["position_scale"] <= 0.25
        
        # List endpoint (no snapshots)
        with patch("jgod.decision_v3.service.list_snapshots") as mock_list:
            mock_list.return_value = []
            
            list_response = client.get("/api/v1/decision-v3/list/NO_SYMBOL?n=20")
            assert list_response.status_code == 200, f"Expected 200 even with no snapshots, got {list_response.status_code}: {list_response.text}"
            
            list_data = list_response.json()
            assert list_data["items"] == []
            assert list_data["total"] == 0

