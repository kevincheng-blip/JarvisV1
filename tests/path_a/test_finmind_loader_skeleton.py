"""
Tests for FinMindPathADataLoader skeleton.

These tests do NOT call the real FinMind API. Instead, they use a dummy
FinMind client that returns small in-memory DataFrames, to validate:

- Column mapping (open/high/low/close/volume)
- Output shapes/formats for price_frame and feature_frame
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from jgod.path_a.path_a_schema import PathAConfig
from jgod.path_a.finmind_loader import FinMindPathADataLoader, FinMindClient


@dataclass
class DummyFinMindClient(FinMindClient):
    """
    Simple in-memory FinMind client for testing.
    
    It ignores stock_id and always returns the same 3-day price series,
    with columns:
        date, stock_id, open, max, min, close, Trading_Volume
    """
    
    def taiwan_stock_daily(
        self,
        stock_id: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
        data = {
            "date": dates,
            "stock_id": [stock_id] * 3,
            "open": [100.0, 101.0, 102.0],
            "max": [101.0, 102.0, 103.0],
            "min": [99.0, 100.0, 101.0],
            "close": [100.5, 101.5, 102.5],
            "Trading_Volume": [1000, 1100, 1200],
        }
        return pd.DataFrame(data)


def _build_config(universe: List[str]) -> PathAConfig:
    return PathAConfig(
        start_date="2024-01-01",
        end_date="2024-01-10",
        universe=universe,
        rebalance_frequency="M",
        experiment_name="test_finmind_loader",
    )


def test_finmind_loader_price_frame_shape_and_columns():
    universe = ["2330.TW", "2317.TW"]
    config = _build_config(universe)
    
    client = DummyFinMindClient()
    loader = FinMindPathADataLoader(client=client)
    
    price_frame = loader.load_price_frame(config=config)
    
    # index should be DatetimeIndex and non-empty
    assert isinstance(price_frame.index, pd.DatetimeIndex)
    assert not price_frame.empty
    
    # columns should be MultiIndex (symbol, field)
    assert isinstance(price_frame.columns, pd.MultiIndex)
    assert set(price_frame.columns.names) == {"symbol", "field"}
    
    # check that each symbol has the expected fields
    fields = {"open", "high", "low", "close", "volume"}
    for symbol in universe:
        symbol_fields = set(price_frame.loc[:, symbol].columns)
        assert fields.issubset(symbol_fields)


def test_finmind_loader_feature_frame_shape_and_features():
    universe = ["2330.TW", "2317.TW"]
    config = _build_config(universe)
    
    client = DummyFinMindClient()
    loader = FinMindPathADataLoader(client=client)
    
    feature_frame = loader.load_feature_frame(config=config)
    
    # index should be MultiIndex (date, symbol)
    assert isinstance(feature_frame.index, pd.MultiIndex)
    assert feature_frame.index.names == ["date", "symbol"]
    
    # feature columns should include the two basic features
    assert "daily_return_1d" in feature_frame.columns
    assert "rolling_vol_5d" in feature_frame.columns
    
    # there should be len(dates) * len(universe) rows
    dates = feature_frame.index.get_level_values("date").unique()
    assert len(feature_frame) == len(dates) * len(universe)

