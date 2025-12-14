"""
Contract tests for Market Data Time Series Service (MDTS)
"""

import pytest
from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot


def test_mdts_fetch_single_date():
    """Test fetching OHLCV for a single date."""
    mdts = MarketDataService(use_mock=True)
    
    snapshot = mdts.fetch_ohlcv("2330", "2024-01-15")
    
    assert snapshot is not None
    assert snapshot.symbol == "2330"
    assert snapshot.date == "2024-01-15"
    assert snapshot.open > 0
    assert snapshot.high >= snapshot.low
    assert snapshot.close > 0
    assert snapshot.volume >= 0


def test_mdts_fetch_date_range():
    """Test fetching OHLCV for a date range."""
    mdts = MarketDataService(use_mock=True)
    
    snapshots = mdts.fetch_ohlcv_range("2330", "2024-01-01", "2024-01-31")
    
    assert len(snapshots) > 0
    assert all(s.symbol == "2330" for s in snapshots)
    assert snapshots[0].date == "2024-01-01"
    assert snapshots[-1].date == "2024-01-31"
    
    # Check chronological order
    dates = [s.date for s in snapshots]
    assert dates == sorted(dates)


def test_mdts_deterministic_mock():
    """Test that mock data is deterministic."""
    mdts = MarketDataService(use_mock=True)
    
    snapshot1 = mdts.fetch_ohlcv("2330", "2024-01-15")
    snapshot2 = mdts.fetch_ohlcv("2330", "2024-01-15")
    
    assert snapshot1.open == snapshot2.open
    assert snapshot1.high == snapshot2.high
    assert snapshot1.low == snapshot2.low
    assert snapshot1.close == snapshot2.close
    assert snapshot1.volume == snapshot2.volume


def test_mdts_ohlcv_snapshot_to_dict():
    """Test OHLCVSnapshot.to_dict()."""
    snapshot = OHLCVSnapshot(
        symbol="2330",
        date="2024-01-15",
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1000000.0,
    )
    
    d = snapshot.to_dict()
    
    assert d["symbol"] == "2330"
    assert d["date"] == "2024-01-15"
    assert d["open"] == 100.0
    assert d["high"] == 105.0
    assert d["low"] == 99.0
    assert d["close"] == 104.0
    assert d["volume"] == 1000000.0

