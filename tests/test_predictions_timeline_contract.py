"""
J-GOD Predictions Timeline API Contract Test

Tests the prediction timeline endpoint contract:
- Returns 200 with valid JSON structure
- Handles missing data gracefully (empty items array)
- Response shape matches expected schema
"""

from fastapi.testclient import TestClient
from jgod.api.main import app

client = TestClient(app)


def test_predictions_timeline_contract():
    """Test prediction timeline endpoint contract"""
    # Test with a symbol that might exist
    symbol = "2330"
    
    response = client.get(f"/api/v1/predictions/timeline/{symbol}", params={"limit": 10})
    
    # Should return 200 even if no data (empty items array)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Verify JSON structure
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "symbol" in data, "Response should have 'symbol' field"
    assert "start_date" in data, "Response should have 'start_date' field"
    assert "end_date" in data, "Response should have 'end_date' field"
    assert "items" in data, "Response should have 'items' field"
    
    # Verify types
    assert isinstance(data["symbol"], str), "symbol should be a string"
    assert isinstance(data["start_date"], str) or data["start_date"] == "", "start_date should be a string or empty"
    assert isinstance(data["end_date"], str) or data["end_date"] == "", "end_date should be a string or empty"
    assert isinstance(data["items"], list), "items should be a list"
    
    # If items exist, verify structure
    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "date" in item, "Timeline item should have 'date' field"
        assert "raw_score" in item, "Timeline item should have 'raw_score' field"
        assert "final_score" in item, "Timeline item should have 'final_score' field"
        assert "signal" in item, "Timeline item should have 'signal' field"


def test_predictions_timeline_empty_symbol():
    """Test timeline endpoint with symbol that doesn't exist (should return empty items)"""
    symbol = "NONEXISTENT999"
    
    response = client.get(f"/api/v1/predictions/timeline/{symbol}", params={"limit": 10})
    
    # Should return 200 with empty items (not 404)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["symbol"] == symbol
    assert isinstance(data["items"], list)
    # Items can be empty, that's fine


def test_predictions_timeline_limit_parameter():
    """Test timeline endpoint respects limit parameter"""
    symbol = "2330"
    
    response = client.get(f"/api/v1/predictions/timeline/{symbol}", params={"limit": 5})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5, f"Should return at most 5 items, got {len(data['items'])}"

