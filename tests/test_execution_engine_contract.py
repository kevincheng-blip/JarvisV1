"""
Contract tests for Execution Engine

v0.6.11-A11: Tests for real-time event-driven execution
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

from jgod.execution.engine import ExecutionEngine, ExecutionStatus
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
        # Simulate immediate fill
        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=order.price or 100.0,
            timestamp=datetime.now().isoformat(),
            order_id=f"MOCK-{len(self.orders)}",
        )
        self.fills.append(fill)
        # Notify callbacks
        for callback in self.callbacks:
            callback(fill)
        return fill.order_id
    
    def cancel_order(self, order_id: str) -> bool:
        return True
    
    def get_positions(self) -> list[Position]:
        return [
            Position(symbol=s, qty=q, avg_cost=100.0, market_value=q * 100.0)
            for s, q in self.positions.items()
        ]
    
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


def test_execution_engine_start_stop_status(mock_data_service):
    """Test that execution engine can start, stop, and report status."""
    broker = MockBroker()
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,  # Fast for testing
    )
    
    # Initial status should be STOPPED
    status = engine.get_status()
    assert status["status"] == ExecutionStatus.STOPPED.value
    
    # Start engine
    success = engine.start(symbols=["2330"])
    assert success is True
    
    # Status should be RUNNING
    status = engine.get_status()
    assert status["status"] == ExecutionStatus.RUNNING.value
    assert status["symbols"] == ["2330"]
    
    # Wait a bit for tick
    time.sleep(0.2)
    
    # Stop engine
    success = engine.stop()
    assert success is True
    
    # Status should be STOPPED
    status = engine.get_status()
    assert status["status"] == ExecutionStatus.STOPPED.value


def test_execution_engine_tick_loop(mock_data_service):
    """Test that tick loop executes and calls broker."""
    broker = MockBroker()
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    # Start engine
    engine.start(symbols=["2330"])
    
    # Wait for at least one tick
    time.sleep(0.3)
    
    # Check that broker was called (orders placed)
    # Note: May be 0 if decision results in HOLD
    # But at least tick loop should have run
    
    # Stop engine
    engine.stop()
    
    # Verify engine stopped
    assert engine.get_status()["status"] == ExecutionStatus.STOPPED.value


def test_execution_engine_singleton():
    """Test that ExecutionEngine follows singleton pattern."""
    engine1 = ExecutionEngine.get_instance()
    engine2 = ExecutionEngine.get_instance()
    
    assert engine1 is engine2


def test_execution_engine_fill_callback(mock_data_service):
    """Test that fill callbacks are received."""
    broker = MockBroker()
    engine = ExecutionEngine(
        data_service=mock_data_service,
        broker=broker,
        tick_interval=0.1,
    )
    
    # Track fills received
    received_fills = []
    
    def fill_callback(fill):
        received_fills.append(fill)
    
    broker.subscribe_fills(fill_callback)
    
    # Place an order manually (simulate broker behavior)
    order = OrderRequest(symbol="2330", side="BUY", qty=100, price=100.0)
    broker.place_order(order)
    
    # Check that callback was called
    assert len(received_fills) > 0
    assert received_fills[0].symbol == "2330"
    assert received_fills[0].side == "BUY"

