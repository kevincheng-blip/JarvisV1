"""
Contract tests for Virtual Ledger
"""

import pytest
from jgod.execution.virtual_ledger import VirtualLedger, PositionState, FEE_RATE, SELL_TAX_RATE


def test_buy_updates_qty_avg_cost_cash():
    """Test that buy updates qty, avg_cost, and cash correctly."""
    ledger = VirtualLedger(symbol="2330", cash=100000.0)
    ledger.mark_to_market("2330", 100.0)
    
    # Buy 100 shares at 100
    result = ledger.buy("2330", 100, 100.0)
    
    assert result["success"] is True
    assert result["qty_executed"] == 100
    
    pos = ledger.positions["2330"]
    assert pos.qty == 100
    assert pos.avg_cost == 100.0  # First buy, avg_cost = price
    assert ledger.cash < 100000.0  # Cash reduced
    
    # Buy more 50 shares at 110 (weighted average)
    result2 = ledger.buy("2330", 50, 110.0)
    assert result2["success"] is True
    assert pos.qty == 150
    # Weighted avg: (100*100 + 50*110) / 150 = 103.33...
    assert abs(pos.avg_cost - 103.33) < 0.1


def test_sell_updates_realized_pnl_and_reduces_qty():
    """Test that sell updates realized P&L and reduces qty."""
    ledger = VirtualLedger(symbol="2330", cash=100000.0)
    ledger.mark_to_market("2330", 100.0)
    
    # Buy 100 shares at 100
    ledger.buy("2330", 100, 100.0)
    cash_after_buy = ledger.cash
    
    # Sell 50 shares at 120 (profit)
    result = ledger.sell("2330", 50, 120.0)
    
    assert result["success"] is True
    assert result["qty_executed"] == 50
    assert result["realized_pnl"] > 0  # Profit
    
    pos = ledger.positions["2330"]
    assert pos.qty == 50
    assert ledger.realized_pnl > 0
    assert ledger.cash > cash_after_buy  # Cash increased from post-buy amount


def test_mark_to_market_updates_unrealized_and_nav():
    """Test that mark_to_market updates unrealized P&L and NAV."""
    ledger = VirtualLedger(symbol="2330", cash=100000.0)
    ledger.mark_to_market("2330", 100.0)
    
    # Buy 100 shares at 100
    ledger.buy("2330", 100, 100.0)
    
    initial_nav = ledger.nav
    initial_unrealized = ledger.unrealized_pnl
    
    # Mark to market at 110 (unrealized profit)
    ledger.mark_to_market("2330", 110.0)
    
    assert ledger.unrealized_pnl > initial_unrealized
    assert ledger.nav > initial_nav


def test_cannot_sell_more_than_qty():
    """Test that selling more than available qty is clamped."""
    ledger = VirtualLedger(symbol="2330", cash=100000.0)
    ledger.mark_to_market("2330", 100.0)
    
    # Buy 100 shares
    ledger.buy("2330", 100, 100.0)
    
    # Try to sell 200 shares (more than owned)
    result = ledger.sell("2330", 200, 120.0)
    
    # Should clamp to 100
    assert result["success"] is True
    assert result["qty_executed"] == 100  # Clamped to available
    
    pos = ledger.positions["2330"]
    assert pos.qty == 0  # All sold


def test_cannot_buy_with_insufficient_cash():
    """Test that buy fails gracefully when cash is insufficient."""
    ledger = VirtualLedger(symbol="2330", cash=1000.0)
    ledger.mark_to_market("2330", 100.0)
    
    # Try to buy 100 shares at 100 (cost = 10000 + fee)
    result = ledger.buy("2330", 100, 100.0)
    
    # Should fail or clamp
    assert result["success"] is False or result["qty_executed"] < 100


def test_snapshot_returns_correct_structure():
    """Test that snapshot returns correct dict structure."""
    ledger = VirtualLedger(symbol="2330", cash=100000.0)
    ledger.mark_to_market("2330", 100.0)
    ledger.buy("2330", 100, 100.0)
    
    snapshot = ledger.snapshot("2330")
    
    assert "symbol" in snapshot
    assert "cash" in snapshot
    assert "position" in snapshot
    assert "realized_pnl" in snapshot
    assert "unrealized_pnl" in snapshot
    assert "nav" in snapshot
    assert snapshot["position"]["qty"] == 100

