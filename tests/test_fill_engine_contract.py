"""
Contract tests for Fill Engine
"""

import pytest
from jgod.execution.fill_engine import FillEngine, OrderFill
from jgod.execution.order_engine import OrderRequest
from jgod.data.market_data_service import OHLCVSnapshot


def test_fill_engine_hold_order():
    """Test that HOLD orders result in no fill."""
    ohlcv = OHLCVSnapshot(
        symbol="2330",
        date="2024-01-15",
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1000000.0,
    )
    
    order = OrderRequest(
        symbol="2330",
        side="HOLD",
        qty=0,
        reason="HOLD",
        target_position_scale=0.5,
        current_position_scale=0.5,
    )
    
    fill = FillEngine.execute(order, ohlcv)
    
    assert fill.side == "HOLD"
    assert fill.qty_executed == 0
    assert fill.fee == 0.0
    assert fill.tax == 0.0
    assert fill.slippage == 0.0


def test_fill_engine_buy_order():
    """Test BUY order execution with slippage and fees."""
    ohlcv = OHLCVSnapshot(
        symbol="2330",
        date="2024-01-15",
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1000000.0,
    )
    
    order = OrderRequest(
        symbol="2330",
        side="BUY",
        qty=100,
        reason="Buy 100 shares",
        target_position_scale=0.5,
        current_position_scale=0.0,
    )
    
    fill = FillEngine.execute(order, ohlcv)
    
    assert fill.side == "BUY"
    assert fill.qty_executed == 100
    assert fill.fill_price > ohlcv.close  # Slippage increases price
    assert fill.fill_price <= ohlcv.high  # Cannot exceed high
    assert fill.fee > 0
    assert fill.tax == 0.0  # No tax on BUY
    assert fill.slippage >= 0


def test_fill_engine_sell_order():
    """Test SELL order execution with slippage, fees, and tax."""
    ohlcv = OHLCVSnapshot(
        symbol="2330",
        date="2024-01-15",
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1000000.0,
    )
    
    order = OrderRequest(
        symbol="2330",
        side="SELL",
        qty=100,
        reason="Sell 100 shares",
        target_position_scale=0.0,
        current_position_scale=0.5,
    )
    
    fill = FillEngine.execute(order, ohlcv)
    
    assert fill.side == "SELL"
    assert fill.qty_executed == 100
    assert fill.fill_price < ohlcv.close  # Slippage decreases price
    assert fill.fill_price >= ohlcv.low  # Cannot go below low
    assert fill.fee > 0
    assert fill.tax > 0  # Tax on SELL
    assert fill.slippage >= 0


def test_fill_engine_total_cost():
    """Test OrderFill.total_cost() calculation."""
    fill_buy = OrderFill(
        symbol="2330",
        side="BUY",
        qty_executed=100,
        fill_price=104.0,
        fee=14.82,
        tax=0.0,
        slippage=0.1,
        reason="Buy",
    )
    
    # BUY: notional + fee
    assert fill_buy.total_cost() == (100 * 104.0) + 14.82
    
    fill_sell = OrderFill(
        symbol="2330",
        side="SELL",
        qty_executed=100,
        fill_price=104.0,
        fee=14.82,
        tax=31.2,
        slippage=0.05,
        reason="Sell",
    )
    
    # SELL: notional - fee - tax
    assert fill_sell.total_cost() == (100 * 104.0) - 14.82 - 31.2

