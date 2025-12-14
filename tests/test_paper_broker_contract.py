"""
Contract tests for Paper Trading Broker Adapter

v0.6.11-A11: Tests for PaperTradingAdapter
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from jgod.broker.paper_adapter import PaperTradingAdapter
from jgod.broker.interface import OrderRequest, Fill


@pytest.fixture
def paper_broker():
    """Create PaperTradingAdapter instance."""
    return PaperTradingAdapter(initial_cash=1_000_000.0, use_mock_mdts=True)


def test_paper_broker_place_order_updates_ledger(paper_broker):
    """Test that placing order updates ledger."""
    initial_cash = paper_broker.ledger.cash
    
    # Place BUY order
    order = OrderRequest(
        symbol="2330",
        side="BUY",
        qty=100,
        price=100.0,
    )
    
    order_id = paper_broker.place_order(order)
    
    # Check order ID generated
    assert order_id is not None
    assert order_id.startswith("PAPER-")
    
    # Check ledger updated (cash decreased)
    assert paper_broker.ledger.cash < initial_cash
    
    # Check position created
    pos = paper_broker.ledger.positions.get("2330")
    assert pos is not None
    assert pos.qty == 100


def test_paper_broker_get_positions(paper_broker):
    """Test that get_positions returns current positions."""
    # Place order to create position
    order = OrderRequest(symbol="2330", side="BUY", qty=100, price=100.0)
    paper_broker.place_order(order)
    
    positions = paper_broker.get_positions()
    
    # Should have one position
    assert len(positions) > 0
    pos = next((p for p in positions if p.symbol == "2330"), None)
    assert pos is not None
    assert pos.qty == 100


def test_paper_broker_get_account_balance(paper_broker):
    """Test that get_account_balance returns correct balance."""
    balance = paper_broker.get_account_balance()
    
    assert balance.cash == 1_000_000.0
    assert balance.equity >= balance.cash  # Equity includes positions
    assert balance.margin_used == 0.0  # Paper trading no margin


def test_paper_broker_subscribe_fills(paper_broker):
    """Test that fill callbacks work."""
    received_fills = []
    
    def fill_callback(fill: Fill):
        received_fills.append(fill)
    
    paper_broker.subscribe_fills(fill_callback)
    
    # Place order
    order = OrderRequest(symbol="2330", side="BUY", qty=100, price=100.0)
    paper_broker.place_order(order)
    
    # Check callback was called
    assert len(received_fills) > 0
    assert received_fills[0].symbol == "2330"
    assert received_fills[0].side == "BUY"
    assert received_fills[0].qty == 100


def test_paper_broker_hold_order(paper_broker):
    """Test that HOLD orders return special order ID."""
    order = OrderRequest(symbol="2330", side="HOLD", qty=0)
    
    order_id = paper_broker.place_order(order)
    
    # HOLD orders should return special ID
    assert order_id.startswith("HOLD-")
    
    # Ledger should not change
    assert paper_broker.ledger.cash == 1_000_000.0


def test_paper_broker_cancel_order(paper_broker):
    """Test that cancel_order works (no-op for paper trading)."""
    order = OrderRequest(symbol="2330", side="BUY", qty=100, price=100.0)
    order_id = paper_broker.place_order(order)
    
    # Cancel should succeed (no-op)
    success = paper_broker.cancel_order(order_id)
    assert success is True

