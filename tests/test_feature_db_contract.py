"""
Contract tests for Feature DB/Cache

v0.6.7-A7.5: Tests for cache hit/miss, version control, and deterministic computation
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
import tempfile
import shutil

from jgod.data.feature_models import FeatureSchema
from jgod.data.feature_service import FeatureService
from jgod.data.feature_storage import save_feature, load_feature, has_feature
from jgod.data.feature_computer import compute_features
from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot


@pytest.fixture
def tmp_storage_path(tmp_path, monkeypatch):
    """Create temporary storage path for tests."""
    storage_dir = tmp_path / "data" / "features"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_file = storage_dir / "features.jsonl"
    
    # Patch the storage path function
    def mock_get_storage_path():
        return storage_file
    
    monkeypatch.setattr("jgod.data.feature_storage._get_storage_path", mock_get_storage_path)
    
    yield storage_file


@pytest.fixture
def mock_mdts():
    """Create mock MarketDataService."""
    mdts = MagicMock(spec=MarketDataService)
    
    # Mock OHLCV series
    ohlcv_series = [
        OHLCVSnapshot(symbol="2330", date="2024-01-01", open=100.0, high=105.0, low=99.0, close=104.0, volume=1000000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-02", open=104.0, high=108.0, low=103.0, close=107.0, volume=1100000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-03", open=107.0, high=110.0, low=106.0, close=109.0, volume=1200000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-04", open=109.0, high=112.0, low=108.0, close=111.0, volume=1300000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-05", open=111.0, high=114.0, low=110.0, close=113.0, volume=1400000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-06", open=113.0, high=116.0, low=112.0, close=115.0, volume=1500000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-07", open=115.0, high=118.0, low=114.0, close=117.0, volume=1600000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-08", open=117.0, high=120.0, low=116.0, close=119.0, volume=1700000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-09", open=119.0, high=122.0, low=118.0, close=121.0, volume=1800000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-10", open=121.0, high=124.0, low=120.0, close=123.0, volume=1900000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-11", open=123.0, high=126.0, low=122.0, close=125.0, volume=2000000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-12", open=125.0, high=128.0, low=124.0, close=127.0, volume=2100000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-13", open=127.0, high=130.0, low=126.0, close=129.0, volume=2200000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-14", open=129.0, high=132.0, low=128.0, close=131.0, volume=2300000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-15", open=131.0, high=134.0, low=130.0, close=133.0, volume=2400000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-16", open=133.0, high=136.0, low=132.0, close=135.0, volume=2500000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-17", open=135.0, high=138.0, low=134.0, close=137.0, volume=2600000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-18", open=137.0, high=140.0, low=136.0, close=139.0, volume=2700000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-19", open=139.0, high=142.0, low=138.0, close=141.0, volume=2800000.0),
        OHLCVSnapshot(symbol="2330", date="2024-01-20", open=141.0, high=144.0, low=140.0, close=143.0, volume=2900000.0),
    ]
    
    mdts.fetch_ohlcv_range.return_value = ohlcv_series
    
    return mdts


def test_feature_service_cache_hit_skip_recompute(tmp_storage_path, mock_mdts):
    """Test that cache hit skips recomputation."""
    service = FeatureService(market_data_service=mock_mdts)
    
    # First call: cache miss → compute + save
    feature1 = service.get_feature("2330", "2024-01-20", version="v1.0", lookback=20)
    
    # Verify MDTS was called
    assert mock_mdts.fetch_ohlcv_range.called
    
    # Reset mock call count
    mock_mdts.reset_mock()
    
    # Second call: cache hit → should NOT call MDTS
    feature2 = service.get_feature("2330", "2024-01-20", version="v1.0", lookback=20)
    
    # Verify MDTS was NOT called again
    assert not mock_mdts.fetch_ohlcv_range.called
    
    # Verify features are the same
    assert feature1.features == feature2.features
    assert feature1.symbol == feature2.symbol
    assert feature1.date == feature2.date
    assert feature1.version == feature2.version


def test_feature_version_bumps_force_recompute(tmp_storage_path, mock_mdts):
    """Test that version bumps force recompute and store separately."""
    service = FeatureService(market_data_service=mock_mdts)
    
    # Compute with v1.0
    feature_v1 = service.get_feature("2330", "2024-01-20", version="v1.0", lookback=20)
    
    # Reset mock
    mock_mdts.reset_mock()
    
    # Compute with v1.1 (different version)
    feature_v1_1 = service.get_feature("2330", "2024-01-20", version="v1.1", lookback=20)
    
    # Verify MDTS was called again (cache miss due to version change)
    assert mock_mdts.fetch_ohlcv_range.called
    
    # Verify both versions exist in storage
    assert has_feature("2330", "2024-01-20", "v1.0")
    assert has_feature("2330", "2024-01-20", "v1.1")
    
    # Verify they are different entries
    loaded_v1 = load_feature("2330", "2024-01-20", "v1.0")
    loaded_v1_1 = load_feature("2330", "2024-01-20", "v1.1")
    
    assert loaded_v1 is not None
    assert loaded_v1_1 is not None
    assert loaded_v1.version == "v1.0"
    assert loaded_v1_1.version == "v1.1"


def test_deterministic_features_same_input_same_output():
    """Test that same OHLCV series produces same features."""
    # Create deterministic OHLCV series
    ohlcv_series = [
        {"date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 99.0, "close": 104.0, "volume": 1000000.0},
        {"date": "2024-01-02", "open": 104.0, "high": 108.0, "low": 103.0, "close": 107.0, "volume": 1100000.0},
        {"date": "2024-01-03", "open": 107.0, "high": 110.0, "low": 106.0, "close": 109.0, "volume": 1200000.0},
        {"date": "2024-01-04", "open": 109.0, "high": 112.0, "low": 108.0, "close": 111.0, "volume": 1300000.0},
        {"date": "2024-01-05", "open": 111.0, "high": 114.0, "low": 110.0, "close": 113.0, "volume": 1400000.0},
        {"date": "2024-01-06", "open": 113.0, "high": 116.0, "low": 112.0, "close": 115.0, "volume": 1500000.0},
        {"date": "2024-01-07", "open": 115.0, "high": 118.0, "low": 114.0, "close": 117.0, "volume": 1600000.0},
        {"date": "2024-01-08", "open": 117.0, "high": 120.0, "low": 116.0, "close": 119.0, "volume": 1700000.0},
        {"date": "2024-01-09", "open": 119.0, "high": 122.0, "low": 118.0, "close": 121.0, "volume": 1800000.0},
        {"date": "2024-01-10", "open": 121.0, "high": 124.0, "low": 120.0, "close": 123.0, "volume": 1900000.0},
        {"date": "2024-01-11", "open": 123.0, "high": 126.0, "low": 122.0, "close": 125.0, "volume": 2000000.0},
        {"date": "2024-01-12", "open": 125.0, "high": 128.0, "low": 124.0, "close": 127.0, "volume": 2100000.0},
        {"date": "2024-01-13", "open": 127.0, "high": 130.0, "low": 126.0, "close": 129.0, "volume": 2200000.0},
        {"date": "2024-01-14", "open": 129.0, "high": 132.0, "low": 128.0, "close": 131.0, "volume": 2300000.0},
        {"date": "2024-01-15", "open": 131.0, "high": 134.0, "low": 130.0, "close": 133.0, "volume": 2400000.0},
        {"date": "2024-01-16", "open": 133.0, "high": 136.0, "low": 132.0, "close": 135.0, "volume": 2500000.0},
        {"date": "2024-01-17", "open": 135.0, "high": 138.0, "low": 134.0, "close": 137.0, "volume": 2600000.0},
        {"date": "2024-01-18", "open": 137.0, "high": 140.0, "low": 136.0, "close": 139.0, "volume": 2700000.0},
        {"date": "2024-01-19", "open": 139.0, "high": 142.0, "low": 138.0, "close": 141.0, "volume": 2800000.0},
        {"date": "2024-01-20", "open": 141.0, "high": 144.0, "low": 140.0, "close": 143.0, "volume": 2900000.0},
    ]
    
    # Compute features twice
    features1 = compute_features(ohlcv_series, version="v1.0")
    features2 = compute_features(ohlcv_series, version="v1.0")
    
    # Verify deterministic: same input → same output
    assert features1 == features2
    
    # Verify specific features exist and are consistent
    assert "SMA_5" in features1
    assert "SMA_20" in features1
    assert "RSI_14" in features1
    assert "VOL_MEAN_20" in features1
    assert "RET_1D" in features1
    
    # Verify values are consistent (not None for sufficient data)
    assert features1["SMA_5"] is not None
    assert features1["SMA_20"] is not None
    assert features1["RSI_14"] is not None
    assert features1["VOL_MEAN_20"] is not None
    assert features1["RET_1D"] is not None
    
    # Verify values match between calls
    assert features1["SMA_5"] == features2["SMA_5"]
    assert features1["SMA_20"] == features2["SMA_20"]
    assert features1["RSI_14"] == features2["RSI_14"]
    assert features1["VOL_MEAN_20"] == features2["VOL_MEAN_20"]
    assert features1["RET_1D"] == features2["RET_1D"]

