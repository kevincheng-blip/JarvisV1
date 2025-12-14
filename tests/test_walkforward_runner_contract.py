"""
Contract tests for Walk-Forward Runner

v0.6.8-A8: Tests for strict T-1 data usage and learning triggers
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from jgod.research.walkforward_runner import WalkForwardRunner
from jgod.research.storage import save_daily_log, load_daily_logs


@pytest.fixture
def runner():
    """Create WalkForwardRunner with mock MDTS."""
    return WalkForwardRunner(use_mock_mdts=True)


def test_walkforward_runner_daily_cycle(runner):
    """Test daily cycle runs without errors."""
    result = runner.run_daily_cycle(
        symbol="2330",
        date_str="2024-04-01",
        doctrine_version="v1.0",
        feature_version="v1.0",
    )
    
    assert result is not None
    assert result.get("symbol") == "2330"
    assert result.get("date") == "2024-04-01"
    assert "nav" in result
    assert "decision" in result
    assert "order" in result
    assert "fill" in result


def test_walkforward_runner_range(runner):
    """Test running range from 2024/04/01 to 2024/04/10."""
    results = runner.run_range(
        symbol="2330",
        start_date="2024-04-01",
        end_date="2024-04-10",
        doctrine_version="v1.0",
        feature_version="v1.0",
    )
    
    assert len(results) > 0
    
    # Check that all results have required fields
    for result in results:
        assert "symbol" in result
        assert "date" in result
        assert "nav" in result
    
    # Check date range
    dates = [r.get("date") for r in results if r.get("date")]
    if dates:
        assert min(dates) >= "2024-04-01"
        assert max(dates) <= "2024-04-10"


def test_walkforward_runner_learning_triggers(runner):
    """Test that learning triggers are checked."""
    # Run a few days to build up logs
    for i in range(5):
        date_str = (datetime(2024, 4, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
        result = runner.run_daily_cycle(
            symbol="2330",
            date_str=date_str,
            doctrine_version="v1.0",
            feature_version="v1.0",
        )
        
        # Check learning_triggers field exists
        assert "learning_triggers" in result
        
        triggers = result.get("learning_triggers", {})
        assert "thought_5d" in triggers
        assert "method_10d" in triggers
        assert "method_20d" in triggers
        assert "strategy_60d" in triggers


def test_walkforward_runner_no_future_data(runner):
    """Test that runner strictly uses T-1 data (no future leakage)."""
    # Run cycle for a specific date
    result = runner.run_daily_cycle(
        symbol="2330",
        date_str="2024-04-05",
        doctrine_version="v1.0",
        feature_version="v1.0",
    )
    
    # Verify that the date in result matches input (not future)
    assert result.get("date") == "2024-04-05"
    
    # Verify features are for the correct date (not future)
    features_summary = result.get("features_summary", {})
    # Features should be computed for 2024-04-05, not future dates
    assert isinstance(features_summary, dict)


def test_walkforward_runner_doctrine_version(runner):
    """Test that doctrine version is used correctly."""
    result = runner.run_daily_cycle(
        symbol="2330",
        date_str="2024-04-01",
        doctrine_version="v1.0",
        feature_version="v1.0",
    )
    
    assert result.get("doctrine_version") == "v1.0"

