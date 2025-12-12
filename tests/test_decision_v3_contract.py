"""
Decision V3 Contract Tests

Tests the API contract for Decision V3 endpoints.
"""

from fastapi.testclient import TestClient
from jgod.api.main import app
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

client = TestClient(app)


def test_decision_v3_stable_case():
    """Test Decision V3 with STABLE metrics returns correct structure"""
    # Mock recommendation data
    mock_snapshot = MagicMock()
    mock_snapshot.items = [
        MagicMock(strategy="trend_follow", weight=0.52),
        MagicMock(strategy="momentum", weight=0.28),
        MagicMock(strategy="mean_reversion", weight=0.20),
    ]
    mock_snapshot.weights = {
        "trend_follow": 0.52,
        "momentum": 0.28,
        "mean_reversion": 0.20,
    }
    mock_snapshot.rationale = {
        "trend_follow": "趨勢斜率為正，適合趨勢跟隨策略",
        "momentum": "動量指標顯示持續上升趨勢",
        "mean_reversion": "上升趨勢中，均值回歸策略權重較低",
    }
    mock_metrics = MagicMock()
    mock_metrics.stability_grade = "STABLE"
    mock_metrics.n_points = 45
    mock_snapshot.metrics = mock_metrics
    
    with patch("jgod.decision_v3.engine.get_recommendation") as mock_get_rec:
        mock_get_rec.return_value = mock_snapshot
        
        response = client.get("/api/v1/decision-v3/decide/2330?mode=performance&limit=60&k=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required fields
        assert "symbol" in data
        assert "selected_primary_strategy" in data
        assert "selected_secondary_strategies" in data
        assert "weights" in data
        assert "risk_plan" in data
        assert "confidence" in data
        assert "explain" in data
        
        # Check primary strategy
        assert data["selected_primary_strategy"] == "trend_follow"
        
        # Check secondary strategies (top 2-3, max 2)
        assert len(data["selected_secondary_strategies"]) <= 2
        assert "momentum" in data["selected_secondary_strategies"]
        
        # Check risk plan
        assert data["risk_plan"]["risk_state"] == "RISK_ON"
        assert data["risk_plan"]["position_scale"] == 0.80  # STABLE case
        assert len(data["risk_plan"]["reasons"]) > 0
        
        # Check confidence (STABLE + top1 weight >= 0.45 should be >= 0.7)
        assert data["confidence"] >= 0.7, f"Expected confidence >= 0.7, got {data['confidence']}"
        
        # Check weights sum ≈ 1.0
        weights_sum = sum(w["weight"] for w in data["weights"])
        assert abs(weights_sum - 1.0) < 0.01, f"Weights sum should be ≈ 1.0, got {weights_sum}"
        
        # Check explain contains key information
        explain = data["explain"]
        assert "2330" in explain or "績效驅動模式" in explain or "訊號驅動模式" in explain
        assert "STABLE" in explain or "穩定" in explain


def test_decision_v3_no_data_case():
    """Test Decision V3 with NO_DATA returns RISK_OFF"""
    # Mock NO_DATA snapshot
    mock_snapshot = MagicMock()
    mock_snapshot.items = []
    mock_snapshot.weights = {}
    mock_snapshot.rationale = {}
    mock_metrics = MagicMock()
    mock_metrics.stability_grade = "NO_DATA"
    mock_metrics.n_points = 0
    mock_snapshot.metrics = mock_metrics
    
    with patch("jgod.decision_v3.engine.get_recommendation") as mock_get_rec:
        mock_get_rec.return_value = mock_snapshot
        
        response = client.get("/api/v1/decision-v3/decide/NO_SYMBOL?mode=performance")
        assert response.status_code == 200, f"Expected 200 even with NO_DATA, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check risk plan is RISK_OFF
        assert data["risk_plan"]["risk_state"] == "RISK_OFF"
        assert data["risk_plan"]["position_scale"] <= 0.25
        
        # Check explain mentions NO_DATA or "暫無資料"
        explain = data["explain"]
        assert "NO_DATA" in explain or "暫無" in explain or "無資料" in explain
        
        # Check confidence is low
        assert data["confidence"] <= 0.3

