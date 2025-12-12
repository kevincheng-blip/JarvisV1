"""
J-GOD Prediction Stability API Contract Test

Tests the prediction stability endpoint contract:
- Returns 200 with valid JSON structure
- Handles missing data gracefully (NO_DATA grade, still 200)
- Response shape matches expected schema
- Limit parameter works correctly
"""

from fastapi.testclient import TestClient
from jgod.api.main import app

client = TestClient(app)


def test_prediction_stability_contract():
    """Test prediction stability endpoint contract"""
    # Test with a symbol that might exist
    symbol = "2330"
    
    response = client.get(f"/api/v1/observer/prediction-stability/{symbol}", params={"limit": 60})
    
    # Should return 200 even if no data (NO_DATA grade)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Verify JSON structure
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "n_points" in data, "Response should have 'n_points' field"
    assert "score_std" in data, "Response should have 'score_std' field"
    assert "max_abs_delta" in data, "Response should have 'max_abs_delta' field"
    assert "trend_slope" in data, "Response should have 'trend_slope' field"
    assert "stability_grade" in data, "Response should have 'stability_grade' field"
    assert "thresholds" in data, "Response should have 'thresholds' field"
    
    # Verify types
    assert isinstance(data["symbol"], str), "symbol should be a string"
    assert isinstance(data["n_points"], int), "n_points should be an integer"
    assert isinstance(data["score_std"], (int, float)), "score_std should be a number"
    assert isinstance(data["max_abs_delta"], (int, float)), "max_abs_delta should be a number"
    assert isinstance(data["trend_slope"], (int, float)), "trend_slope should be a number"
    assert isinstance(data["stability_grade"], str), "stability_grade should be a string"
    assert data["stability_grade"] in ["NO_DATA", "STABLE", "WATCH", "VOLATILE"], \
        f"stability_grade should be one of NO_DATA/STABLE/WATCH/VOLATILE, got {data['stability_grade']}"
    assert isinstance(data["thresholds"], dict), "thresholds should be a dictionary"


def test_prediction_stability_no_data():
    """Test stability endpoint with symbol that doesn't exist (should return NO_DATA)"""
    symbol = "NONEXISTENT999"
    
    response = client.get(f"/api/v1/observer/prediction-stability/{symbol}", params={"limit": 60})
    
    # Should return 200 with NO_DATA grade (not 404)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["symbol"] == symbol
    assert data["n_points"] == 0
    assert data["stability_grade"] == "NO_DATA"
    assert data["score_std"] == 0.0
    assert data["max_abs_delta"] == 0.0
    assert data["trend_slope"] == 0.0


def test_prediction_stability_limit_parameter():
    """Test stability endpoint respects limit parameter"""
    symbol = "2330"
    
    response = client.get(f"/api/v1/observer/prediction-stability/{symbol}", params={"limit": 10})
    
    assert response.status_code == 200
    data = response.json()
    # n_points should be <= limit (if data exists)
    assert data["n_points"] <= 10, f"Should return at most 10 points, got {data['n_points']}"

