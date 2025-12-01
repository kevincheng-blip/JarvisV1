"""
Tests for Path A Schema definitions

v1: Basic tests to ensure schema classes can be instantiated correctly.
"""

import pytest
import pandas as pd
from datetime import datetime

from jgod.path_a.path_a_schema import (
    PathAConfig,
    PathADailyInput,
    PathAFeatureFrame,
    PathAPrediction,
    PathAPortfolioSnapshot,
    PathABacktestResult,
)


def test_path_a_config():
    """Test PathAConfig can be created with default values"""
    config = PathAConfig(
        start_date="2022-01-01",
        end_date="2024-12-31",
        universe=["2330", "2317", "2454"],
    )
    
    assert config.start_date == "2022-01-01"
    assert config.end_date == "2024-12-31"
    assert len(config.universe) == 3
    assert config.rebalance_frequency == "M"  # default
    assert config.initial_nav == 100.0  # default


def test_path_a_daily_input():
    """Test PathADailyInput can be created"""
    date = pd.Timestamp("2024-01-01")
    symbols = ["2330", "2317"]
    
    daily_input = PathADailyInput(
        date=date,
        symbols=symbols,
        open=pd.Series([500.0, 100.0], index=symbols),
        high=pd.Series([510.0, 105.0], index=symbols),
        low=pd.Series([495.0, 98.0], index=symbols),
        close=pd.Series([505.0, 102.0], index=symbols),
        volume=pd.Series([1000000, 500000], index=symbols),
    )
    
    assert daily_input.date == date
    assert len(daily_input.symbols) == 2
    assert daily_input.close["2330"] == 505.0


def test_path_a_portfolio_snapshot():
    """Test PathAPortfolioSnapshot can be created"""
    date = pd.Timestamp("2024-01-01")
    symbols = ["2330", "2317", "2454"]
    
    snapshot = PathAPortfolioSnapshot(
        date=date,
        symbols=symbols,
        weights=pd.Series([0.5, 0.3, 0.2], index=symbols),
        nav=100.0,
        portfolio_return=0.01,
    )
    
    assert snapshot.date == date
    assert snapshot.nav == 100.0
    assert snapshot.portfolio_return == 0.01
    assert snapshot.weights.sum() == pytest.approx(1.0, rel=1e-6)


def test_path_a_backtest_result():
    """Test PathABacktestResult can be created"""
    config = PathAConfig(
        start_date="2022-01-01",
        end_date="2024-12-31",
        universe=["2330"],
    )
    
    dates = pd.date_range("2022-01-01", "2022-01-05", freq="D")
    
    result = PathABacktestResult(
        config=config,
        nav_series=pd.Series([100.0, 101.0, 99.5, 100.5, 102.0], index=dates),
        return_series=pd.Series([0.0, 0.01, -0.015, 0.01, 0.015], index=dates),
        portfolio_snapshots=[],
    )
    
    assert len(result.nav_series) == 5
    assert len(result.return_series) == 5
    assert result.config == config

