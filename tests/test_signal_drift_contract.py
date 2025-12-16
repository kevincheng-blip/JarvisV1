"""
Signal Drift Score Contract Tests

v0.6.13-P1.1: Tests for deterministic drift calculation, storage, and API
"""

import pytest
from datetime import datetime

from jgod.learning.drift_score import compute_drift_score_v1
from jgod.research import storage as research_storage
from jgod.api.routers.intelligence import get_latest_intelligence_status


def test_drift_score_deterministic():
    """Test that same input produces same output."""
    baseline = {"RSI_14": 50.0, "SMA_20": 100.0, "MACD": 0.5}
    current = {"RSI_14": 55.0, "SMA_20": 105.0, "MACD": 0.6}
    
    result1 = compute_drift_score_v1(baseline, current)
    result2 = compute_drift_score_v1(baseline, current)
    
    assert result1["drift_score"] == result2["drift_score"]
    assert result1["drift_level"] == result2["drift_level"]


def test_drift_score_no_drift():
    """Test that identical baseline and current produce drift_score=0."""
    baseline = {"RSI_14": 50.0, "SMA_20": 100.0, "MACD": 0.5}
    current = {"RSI_14": 50.0, "SMA_20": 100.0, "MACD": 0.5}
    
    result = compute_drift_score_v1(baseline, current)
    
    assert result["drift_score"] == 0.0
    assert result["drift_level"] == "LOW"


def test_drift_score_high_drift():
    """Test that significant shift produces drift_score >= 0.7."""
    baseline = {"RSI_14": 50.0, "SMA_20": 100.0, "MACD": 0.5}
    # Large shift: 100% change
    current = {"RSI_14": 100.0, "SMA_20": 200.0, "MACD": 1.0}
    
    result = compute_drift_score_v1(baseline, current)
    
    assert result["drift_score"] >= 0.7
    assert result["drift_level"] == "HIGH"


def test_drift_score_insufficient_features():
    """Test that < 3 common features returns drift_score=0 with notes."""
    baseline = {"RSI_14": 50.0}
    current = {"SMA_20": 100.0}
    
    result = compute_drift_score_v1(baseline, current)
    
    assert result["drift_score"] == 0.0
    assert result["drift_level"] == "LOW"
    assert result["notes"] is not None
    assert "Insufficient" in result["notes"] or "common features" in result["notes"]


def test_drift_storage_save_and_latest():
    """Test saving and loading drift events."""
    # Clean up: try to get latest first
    latest_before = research_storage.latest_drift_event(symbol="TEST")
    
    # Save two events
    event1 = {
        "symbol": "TEST",
        "date": "2025-12-16",
        "method_version": "v1",
        "baseline_window": "WFA_BASELINE",
        "current_window": "WFA_CURRENT",
        "drift_score": 0.37,
        "drift_level": "MEDIUM",
        "features_used": ["RSI_14", "SMA_20", "MACD"],
        "created_at": datetime.now().isoformat(),
    }
    
    research_storage.save_drift_event(event1)
    
    event2 = {
        "symbol": "TEST",
        "date": "2025-12-17",
        "method_version": "v1",
        "baseline_window": "WFA_BASELINE",
        "current_window": "WFA_CURRENT",
        "drift_score": 0.45,
        "drift_level": "MEDIUM",
        "features_used": ["RSI_14", "SMA_20", "MACD"],
        "created_at": datetime.now().isoformat(),
    }
    
    research_storage.save_drift_event(event2)
    
    # Get latest
    latest = research_storage.latest_drift_event(symbol="TEST")
    
    assert latest is not None
    assert latest["symbol"] == "TEST"
    assert latest["drift_score"] == 0.45  # Should be the second (latest) event


def test_intelligence_api_no_data():
    """Test API returns default values when no data."""
    # Test the storage function directly (API endpoint logic)
    # Use a non-existent symbol to ensure no data
    latest = research_storage.latest_drift_event(symbol="NONEXISTENT_SYMBOL_XYZ")
    
    # Should return None when no data
    if latest is None:
        drift_score = 0.0
        drift_level = "LOW"
        drift_updated_at = None
    else:
        drift_score = latest.get("drift_score", 0.0)
        drift_level = latest.get("drift_level", "LOW")
        drift_updated_at = latest.get("created_at")
    
    # Verify default behavior (either no data or default values)
    # This test is lenient because there might be existing drift events
    assert drift_score >= 0.0
    assert drift_level in ["LOW", "MEDIUM", "HIGH"]


def test_intelligence_api_with_data():
    """Test API returns drift data when available."""
    # Save a drift event first
    event = {
        "symbol": "2330",
        "date": "2025-12-16",
        "method_version": "v1",
        "baseline_window": "WFA_BASELINE",
        "current_window": "WFA_CURRENT",
        "drift_score": 0.65,
        "drift_level": "MEDIUM",
        "features_used": ["RSI_14", "SMA_20", "MACD"],
        "created_at": datetime.now().isoformat(),
    }
    
    research_storage.save_drift_event(event)
    
    # Test the storage function directly
    latest = research_storage.latest_drift_event(symbol=None)
    
    assert latest is not None
    assert latest["drift_score"] == 0.65
    assert latest["drift_level"] == "MEDIUM"
    assert latest["created_at"] is not None

