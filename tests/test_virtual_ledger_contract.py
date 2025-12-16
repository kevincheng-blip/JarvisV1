"""
Virtual Ledger Contract Tests

Tests for VirtualLedger core logic (buy, sell, P&L, avg_cost).
"""

import pytest
from jgod.execution.virtual_ledger import VirtualLedger, PositionState, FEE_RATE, SELL_TAX_RATE


def test_virtual_ledger_initialization():
    """Test VirtualLedger initialization"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    assert ledger.symbol == "2330"
    assert ledger.cash == 1_000_000.0
    assert ledger.realized_pnl == 0.0
    assert ledger.unrealized_pnl == 0.0
    assert "2330" in ledger.positions
    assert ledger.positions["2330"].qty == 0
    assert ledger.positions["2330"].avg_cost == 0.0


def test_virtual_ledger_mark_to_market():
    """Test mark_to_market updates NAV and unrealized P&L"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    # Buy some shares
    result = ledger.buy("2330", 1000, 100.0)
    assert result["success"] is True
    
    # Mark to market at higher price
    ledger.mark_to_market("2330", 110.0)
    
    # Check unrealized P&L
    pos = ledger.positions["2330"]
    expected_unrealized = (110.0 - pos.avg_cost) * 1000
    assert abs(ledger.unrealized_pnl - expected_unrealized) < 0.01
    
    # Check NAV
    expected_nav = ledger.cash + (1000 * 110.0)
    assert abs(ledger.nav - expected_nav) < 0.01


def test_virtual_ledger_buy_success():
    """Test successful buy operation"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    price = 100.0
    qty = 1000
    
    result = ledger.buy("2330", qty, price)
    
    assert result["success"] is True
    assert result["qty_executed"] == qty
    assert result["fee"] > 0
    
    # Check position
    pos = ledger.positions["2330"]
    assert pos.qty == qty
    assert pos.avg_cost > 0
    assert pos.avg_cost < price * 1.01  # Should be close to price (with fee)
    
    # Check cash decreased
    notional = qty * price
    fee = notional * FEE_RATE
    expected_cash = 1_000_000.0 - notional - fee
    assert abs(ledger.cash - expected_cash) < 0.01


def test_virtual_ledger_buy_insufficient_cash():
    """Test buy with insufficient cash (should reduce qty)"""
    ledger = VirtualLedger(symbol="2330", cash=1000.0)  # Low cash
    price = 100.0
    qty = 1000  # Too much
    
    result = ledger.buy("2330", qty, price)
    
    # Should succeed but with reduced qty
    if result["success"]:
        assert result["qty_executed"] < qty
        assert result["qty_executed"] > 0
    else:
        # Or fail if can't afford even 1 share
        assert result["message"] is not None


def test_virtual_ledger_sell_success():
    """Test successful sell operation"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    buy_price = 100.0
    sell_price = 110.0
    qty = 1000
    
    # Buy first
    buy_result = ledger.buy("2330", qty, buy_price)
    assert buy_result["success"] is True
    
    initial_cash = ledger.cash
    initial_realized_pnl = ledger.realized_pnl
    
    # Sell
    sell_result = ledger.sell("2330", qty, sell_price)
    
    assert sell_result["success"] is True
    assert sell_result["qty_executed"] == qty
    assert sell_result["fee"] > 0
    assert sell_result["tax"] > 0
    assert sell_result["realized_pnl"] > 0  # Should have profit
    
    # Check position cleared
    pos = ledger.positions["2330"]
    assert pos.qty == 0
    assert pos.avg_cost == 0.0
    
    # Check realized P&L increased
    assert ledger.realized_pnl > initial_realized_pnl
    
    # Check cash increased
    assert ledger.cash > initial_cash


def test_virtual_ledger_sell_insufficient_position():
    """Test sell with insufficient position"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    # Try to sell without buying
    result = ledger.sell("2330", 1000, 100.0)
    
    assert result["success"] is False
    assert result["qty_executed"] == 0
    assert "無" in result["message"] or "不足" in result["message"]


def test_virtual_ledger_sell_partial():
    """Test partial sell (sell less than owned)"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    # Buy 1000 shares
    buy_result = ledger.buy("2330", 1000, 100.0)
    assert buy_result["success"] is True
    
    # Sell 300 shares
    sell_result = ledger.sell("2330", 300, 110.0)
    
    assert sell_result["success"] is True
    assert sell_result["qty_executed"] == 300
    
    # Check position reduced
    pos = ledger.positions["2330"]
    assert pos.qty == 700
    assert pos.avg_cost > 0  # Should maintain avg_cost


def test_virtual_ledger_avg_cost_calculation():
    """Test average cost calculation for multiple buys"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    # First buy: 500 shares @ 100
    result1 = ledger.buy("2330", 500, 100.0)
    assert result1["success"] is True
    pos = ledger.positions["2330"]
    avg_cost_1 = pos.avg_cost
    
    # Second buy: 500 shares @ 110
    result2 = ledger.buy("2330", 500, 110.0)
    assert result2["success"] is True
    pos = ledger.positions["2330"]
    avg_cost_2 = pos.avg_cost
    
    # Average cost should be between 100 and 110
    assert 100.0 < avg_cost_2 < 110.0
    assert avg_cost_2 > avg_cost_1  # Should increase


def test_virtual_ledger_snapshot():
    """Test snapshot generation"""
    ledger = VirtualLedger(symbol="2330", cash=1_000_000.0)
    
    # Buy some shares
    ledger.buy("2330", 1000, 100.0)
    ledger.mark_to_market("2330", 110.0)
    
    snapshot = ledger.snapshot("2330")
    
    assert snapshot["symbol"] == "2330"
    assert snapshot["cash"] == ledger.cash
    assert "position" in snapshot
    assert snapshot["position"]["qty"] == 1000
    assert snapshot["position"]["avg_cost"] > 0
    assert snapshot["realized_pnl"] == ledger.realized_pnl
    assert snapshot["unrealized_pnl"] == ledger.unrealized_pnl
    assert snapshot["nav"] == ledger.nav
    assert snapshot["last_price"] == 110.0
