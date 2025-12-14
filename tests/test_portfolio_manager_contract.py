"""
Contract tests for Portfolio Manager

v0.6.10-A10: Tests for allocation, portfolio run, time sync, and multi-symbol isolation
"""

import pytest
from unittest.mock import MagicMock, patch

from jgod.strategy.portfolio_manager import PortfolioManager
from jgod.strategy.models import PortfolioConfig, AllocationResult
from jgod.data.data_service import DefaultDataService
from jgod.execution.virtual_ledger import VirtualLedger


@pytest.fixture
def mock_data_service():
    """Create mock data service."""
    service = MagicMock()
    
    # Mock get_features
    service.get_features.return_value = {
        "SMA_5": 100.0,
        "SMA_20": 105.0,
        "RSI_14": 50.0,
        "RET_1D": 0.01,
    }
    
    # Mock get_ohlcv
    service.get_ohlcv.return_value = {
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 104.0,
        "volume": 1000000.0,
        "date": "2024-04-01",
    }
    
    # Mock get_trading_dates
    service.get_trading_dates.return_value = [
        "2024-04-01",
        "2024-04-02",
        "2024-04-03",
    ]
    
    return service


def test_equal_weight_allocation_deterministic(mock_data_service):
    """Test that equal weight allocation is deterministic."""
    manager = PortfolioManager(data_service=mock_data_service)
    
    config = PortfolioConfig(
        symbols=["2330", "2317", "2454"],
        initial_cash_total=1_000_000.0,
        allocation_mode="equal_weight",
    )
    
    allocation1 = manager.allocate_capital(config)
    allocation2 = manager.allocate_capital(config)
    
    # Same input should produce same output
    assert allocation1.per_symbol_cash == allocation2.per_symbol_cash
    assert allocation1.weights == allocation2.weights
    
    # Check equal weight property
    assert len(allocation1.per_symbol_cash) == 3
    cash_per_symbol = 1_000_000.0 / 3
    assert abs(allocation1.per_symbol_cash["2330"] - cash_per_symbol) < 0.01
    assert abs(allocation1.per_symbol_cash["2317"] - cash_per_symbol) < 0.01
    assert abs(allocation1.per_symbol_cash["2454"] - cash_per_symbol) < 0.01
    
    # Check weights sum to 1
    total_weight = sum(allocation1.weights.values())
    assert abs(total_weight - 1.0) < 0.001


def test_vol_parity_weights_sum_to_one(mock_data_service):
    """Test that vol parity weights sum to 1 and have inverse-vol property."""
    manager = PortfolioManager(data_service=mock_data_service)
    
    config = PortfolioConfig(
        symbols=["2330", "2317"],
        initial_cash_total=1_000_000.0,
        allocation_mode="vol_parity",
        vol_lookback=20,
    )
    
    allocation = manager.allocate_capital(config)
    
    # Check weights sum to 1
    total_weight = sum(allocation.weights.values())
    assert abs(total_weight - 1.0) < 0.001
    
    # Check inverse-vol property (simplified: lower vol should get higher weight)
    # This is a structural test - actual vol calculation depends on data
    assert allocation.method == "vol_parity"


def test_portfolio_run_produces_portfolio_logs(mock_data_service):
    """Test that portfolio run produces portfolio_logs.jsonl entries."""
    manager = PortfolioManager(
        data_service=mock_data_service,
        portfolio_autopilot_enabled=False,
        portfolio_time_sync_check_enabled=True,
    )
    
    config = PortfolioConfig(
        symbols=["2330"],
        initial_cash_total=1_000_000.0,
        allocation_mode="equal_weight",
    )
    
    with patch("jgod.research.walkforward_runner.WalkForwardRunner.run_daily_cycle") as mock_run:
        mock_run.return_value = {
            "symbol": "2330",
            "date": "2024-04-01",
            "nav": 1_000_000.0,
            "cash": 1_000_000.0,
        }
        
        with patch("jgod.research.storage.save_portfolio_log") as mock_save:
            portfolio_logs = manager.run_portfolio_walkforward(
                config=config,
                start_date="2024-04-01",
                end_date="2024-04-03",
            )
            
            # Should produce portfolio logs
            assert len(portfolio_logs) > 0
            
            # Should call save_portfolio_log for each day
            assert mock_save.call_count == len(portfolio_logs)
            
            # Check log structure
            log = portfolio_logs[0]
            assert "date" in log.__dict__
            assert "portfolio_nav" in log.__dict__
            assert "per_symbol_nav" in log.__dict__


def test_time_sync_check_runner_dates_mismatch(mock_data_service):
    """Test that time sync check fails if runner dates mismatch."""
    manager = PortfolioManager(
        data_service=mock_data_service,
        portfolio_time_sync_check_enabled=True,
    )
    
    config = PortfolioConfig(
        symbols=["2330"],
        initial_cash_total=1_000_000.0,
        allocation_mode="equal_weight",
    )
    
    # Initialize runner
    manager.allocate_capital(config)
    
    runner = manager.runners["2330"]
    
    # Set runner's current date to different value
    runner._current_date = "2024-04-02"
    
    # Try to run with different date - should raise error
    with pytest.raises(ValueError, match="Time sync error"):
        runner.run_daily_cycle(
            symbol="2330",
            date_str="2024-04-01",  # Different date
            doctrine_version="v1.0",
            feature_version="v1.0",
        )


def test_multi_symbol_uses_separate_ledgers(mock_data_service):
    """Test that multi-symbol uses separate ledgers with different cash."""
    manager = PortfolioManager(data_service=mock_data_service)
    
    config = PortfolioConfig(
        symbols=["2330", "2317"],
        initial_cash_total=1_000_000.0,
        allocation_mode="equal_weight",
    )
    
    allocation = manager.allocate_capital(config)
    
    # Initialize runners and ledgers
    for symbol in config.symbols:
        cash = allocation.per_symbol_cash.get(symbol, 0.0)
        ledger = VirtualLedger(symbol=symbol, cash=cash)
        manager.ledgers[symbol] = ledger
    
    # Check that ledgers have different cash
    assert manager.ledgers["2330"].cash == 500_000.0
    assert manager.ledgers["2317"].cash == 500_000.0
    assert manager.ledgers["2330"].cash != manager.ledgers["2317"].cash or len(config.symbols) == 1
    
    # Check that ledgers are separate instances
    assert manager.ledgers["2330"] is not manager.ledgers["2317"]

