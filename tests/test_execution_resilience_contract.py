"""
Contract tests for Execution Engine Resilience

v0.6.12-A12: Tests for state persistence, metrics, alerting, and fault tolerance
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from jgod.execution.engine import ExecutionEngine, ExecutionStatus
from jgod.execution.state_store import ExecutionStateStore
from jgod.monitoring.metrics_logger import MetricsLogger
from jgod.monitoring.alerting_service import AlertingService
from jgod.broker.interface import BrokerAdapterInterface, OrderRequest, Fill, AccountBalance, Position


class MockBroker(BrokerAdapterInterface):
    """Mock broker for testing."""
    
    def __init__(self):
        self.orders = []
        self.fills = []
        self.callbacks = []
        self.cash = 1_000_000.0
        self.positions = {}
    
    def place_order(self, order: OrderRequest) -> str:
        self.orders.append(order)
        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=order.price or 100.0,
            timestamp=datetime.now().isoformat(),
            order_id=f"MOCK-{len(self.orders)}",
        )
        self.fills.append(fill)
        for callback in self.callbacks:
            callback(fill)
        return fill.order_id
    
    def cancel_order(self, order_id: str) -> bool:
        return True
    
    def get_positions(self) -> list[Position]:
        return []
    
    def get_account_balance(self) -> AccountBalance:
        return AccountBalance(cash=self.cash, equity=self.cash)
    
    def subscribe_fills(self, callback):
        self.callbacks.append(callback)


@pytest.fixture
def mock_data_service():
    """Create mock data service."""
    service = MagicMock()
    service.get_latest_data.return_value = {
        "SMA_5": 100.0,
        "SMA_20": 105.0,
        "RSI_14": 50.0,
        "RET_1D": 0.01,
    }
    service.get_ohlcv.return_value = {
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 104.0,
        "volume": 1000000.0,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    return service


def test_state_store_save_load():
    """Test that state_store can save and load state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.json"
        store = ExecutionStateStore(storage_path=state_path)
        
        # Save state
        state = {
            "engine_status": "RUNNING",
            "last_tick_time": "2024-04-01T10:00:00",
            "symbols": ["2330"],
        }
        store.save_state(state)
        
        # Load state
        loaded = store.load_state()
        
        assert loaded is not None
        assert loaded["engine_status"] == "RUNNING"
        assert loaded["last_tick_time"] == "2024-04-01T10:00:00"
        assert loaded["symbols"] == ["2330"]


def test_engine_restart_restores_state(mock_data_service):
    """Test that engine restart restores last_tick_time."""
    broker = MockBroker()
    
    # Create engine and save state
    engine1 = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    engine1._last_tick_time = "2024-04-01T10:00:00"
    engine1._save_state()
    
    # Create new engine instance (simulating restart)
    engine2 = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    # Start engine (should load state)
    engine2.start(symbols=["2330"])
    
    # Check that last_tick_time was restored
    assert engine2._last_tick_time == "2024-04-01T10:00:00"
    
    engine2.stop()


def test_tick_exception_does_not_stop_engine(mock_data_service):
    """Test that tick exception does not stop engine."""
    broker = MockBroker()
    
    # Make data service raise exception
    mock_data_service.get_latest_data.side_effect = Exception("Test error")
    
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    engine.start(symbols=["2330"])
    
    # Wait for at least one tick
    time.sleep(0.3)
    
    # Engine should still be running (not ERROR)
    assert engine.status == ExecutionStatus.RUNNING
    
    # Should have logged error
    assert engine.metrics_logger.counters["ticks_error"] > 0
    
    engine.stop()


def test_alerts_are_recorded(mock_data_service):
    """Test that alerts are recorded."""
    broker = MockBroker()
    
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    # Send test alert
    engine.alerting_service.send_alert(
        level="WARN",
        message="Test alert",
        context={"test": True},
    )
    
    # Check alert was recorded
    alerts = engine.alerting_service.get_alerts(limit=10)
    assert len(alerts) > 0
    assert any(a["message"] == "Test alert" for a in alerts)


def test_metrics_snapshot_non_empty(mock_data_service):
    """Test that metrics snapshot is non-empty after ticks."""
    broker = MockBroker()
    
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    engine.start(symbols=["2330"])
    
    # Wait for at least one tick
    time.sleep(0.3)
    
    snapshot = engine.metrics_logger.snapshot()
    
    # Should have metrics
    assert "timestamp" in snapshot
    assert "metrics" in snapshot
    assert "counters" in snapshot
    
    # Should have at least one metric
    assert len(snapshot["metrics"]) > 0 or len(snapshot["counters"]) > 0
    
    engine.stop()


def test_data_service_none_does_not_crash(mock_data_service):
    """Test that data_service returning None does not crash engine."""
    broker = MockBroker()
    
    # Make data service return None
    mock_data_service.get_latest_data.return_value = None
    
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    engine.start(symbols=["2330"])
    
    # Wait for at least one tick
    time.sleep(0.3)
    
    # Engine should still be running
    assert engine.status == ExecutionStatus.RUNNING
    
    # Should have sent WARN alert
    alerts = engine.alerting_service.get_alerts(level="WARN", limit=10)
    assert any("No data" in a["message"] for a in alerts)
    
    engine.stop()

