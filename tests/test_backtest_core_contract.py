"""
Contract tests for Backtest Core
"""

import pytest
from jgod.research.backtest_engine import BacktestEngine, BacktestConfig, BacktestReport


def test_backtest_engine_run_basic():
    """Test basic backtest run."""
    engine = BacktestEngine(use_mock_mdts=True)
    config = BacktestConfig(
        initial_cash=1_000_000.0,
        mode="performance",
        limit=60,
        k=5,
    )
    
    report = engine.run("2330", "2024-01-01", "2024-01-31", config)
    
    assert isinstance(report, BacktestReport)
    assert report.symbol == "2330"
    assert report.start_date == "2024-01-01"
    assert report.end_date == "2024-01-31"
    assert report.initial_cash == 1_000_000.0
    assert report.final_nav >= 0
    assert len(report.daily_log) > 0


def test_backtest_engine_metrics():
    """Test that backtest produces valid metrics."""
    engine = BacktestEngine(use_mock_mdts=True)
    config = BacktestConfig(initial_cash=1_000_000.0)
    
    report = engine.run("2330", "2024-01-01", "2024-01-31", config)
    
    metrics = report.metrics
    assert metrics.total_return is not None
    assert metrics.avg_daily_return is not None
    assert metrics.max_drawdown >= 0
    assert metrics.max_drawdown <= 1.0  # Should be percentage
    assert metrics.sharpe_ratio is not None
    assert metrics.hit_rate >= 0
    assert metrics.hit_rate <= 1.0
    assert metrics.turnover >= 0


def test_backtest_engine_daily_log_structure():
    """Test daily log structure."""
    engine = BacktestEngine(use_mock_mdts=True)
    config = BacktestConfig(initial_cash=1_000_000.0)
    
    report = engine.run("2330", "2024-01-01", "2024-01-15", config)
    
    if len(report.daily_log) > 0:
        log = report.daily_log[0]
        assert "date" in log.__dict__ or hasattr(log, "date")
        assert "nav" in log.__dict__ or hasattr(log, "nav")
        assert "position" in log.__dict__ or hasattr(log, "position")
        assert "realized_pnl" in log.__dict__ or hasattr(log, "realized_pnl")
        assert "ohlcv" in log.__dict__ or hasattr(log, "ohlcv")  # v0.6.7-A7.5
        assert "features_summary" in log.__dict__ or hasattr(log, "features_summary")  # v0.6.7-A7.5
        assert "decision" in log.__dict__ or hasattr(log, "decision")
        assert "order" in log.__dict__ or hasattr(log, "order")
        assert "fill" in log.__dict__ or hasattr(log, "fill")


def test_backtest_engine_empty_date_range():
    """Test backtest with empty date range (no data)."""
    engine = BacktestEngine(use_mock_mdts=True)
    config = BacktestConfig(initial_cash=1_000_000.0)
    
    # Use invalid date range (future dates with no mock data)
    report = engine.run("2330", "2099-01-01", "2099-01-31", config)
    
    assert report.final_nav == config.initial_cash
    assert len(report.daily_log) == 0
    assert report.metrics.total_return == 0.0


def test_backtest_engine_deterministic():
    """Test that backtest is deterministic (same inputs = same outputs)."""
    engine1 = BacktestEngine(use_mock_mdts=True)
    engine2 = BacktestEngine(use_mock_mdts=True)
    config = BacktestConfig(initial_cash=1_000_000.0)
    
    report1 = engine1.run("2330", "2024-01-01", "2024-01-15", config)
    report2 = engine2.run("2330", "2024-01-01", "2024-01-15", config)
    
    assert report1.final_nav == report2.final_nav
    assert report1.metrics.total_return == report2.metrics.total_return
    assert len(report1.daily_log) == len(report2.daily_log)

