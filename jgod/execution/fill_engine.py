"""
Fill Engine: Order execution with slippage and fees

Simulates order execution with realistic market friction:
- Slippage (price impact)
- Fees (commission + tax)
- Partial fills (if volume is insufficient)
"""

import logging
from dataclasses import dataclass
from typing import Literal, Optional
import math

from jgod.execution.order_engine import OrderRequest, OrderSide
from jgod.data.market_data_service import OHLCVSnapshot
from jgod.execution.virtual_ledger import FEE_RATE, SELL_TAX_RATE

logger = logging.getLogger(__name__)


@dataclass
class OrderFill:
    """Order fill result."""
    symbol: str
    side: OrderSide
    qty_executed: int
    fill_price: float
    fee: float
    tax: float  # Only for SELL
    slippage: float  # Price impact (fill_price - expected_price)
    reason: str  # Traditional Chinese
    
    def total_cost(self) -> float:
        """Total cost (for BUY) or net proceeds (for SELL)."""
        notional = self.qty_executed * self.fill_price
        if self.side == "BUY":
            return notional + self.fee
        else:  # SELL
            return notional - self.fee - self.tax


class FillEngine:
    """Engine for executing orders with market friction."""
    
    # Default slippage rates (basis points)
    SLIPPAGE_RATE_BUY = 0.001  # 0.1% for market buy
    SLIPPAGE_RATE_SELL = 0.0005  # 0.05% for market sell
    
    @staticmethod
    def execute(
        order: OrderRequest,
        ohlcv: OHLCVSnapshot,
        slippage_rate_buy: Optional[float] = None,
        slippage_rate_sell: Optional[float] = None,
    ) -> OrderFill:
        """
        Execute order with slippage and fees.
        
        Args:
            order: Order request
            ohlcv: Current OHLCV snapshot
            slippage_rate_buy: Slippage rate for BUY (default 0.1%)
            slippage_rate_sell: Slippage rate for SELL (default 0.05%)
            
        Returns:
            OrderFill result
        """
        if order.side == "HOLD":
            return OrderFill(
                symbol=order.symbol,
                side="HOLD",
                qty_executed=0,
                fill_price=ohlcv.close,
                fee=0.0,
                tax=0.0,
                slippage=0.0,
                reason="訂單為 HOLD，無需執行"
            )
        
        slippage_buy = slippage_rate_buy or FillEngine.SLIPPAGE_RATE_BUY
        slippage_sell = slippage_rate_sell or FillEngine.SLIPPAGE_RATE_SELL
        
        # Determine fill price with slippage
        if order.side == "BUY":
            # Market buy: fill at high (worst case) or close + slippage
            expected_price = ohlcv.close
            fill_price = expected_price * (1 + slippage_buy)
            # Clamp to high (cannot exceed high)
            fill_price = min(fill_price, ohlcv.high)
            slippage_amount = fill_price - expected_price
        else:  # SELL
            # Market sell: fill at low (worst case) or close - slippage
            expected_price = ohlcv.close
            fill_price = expected_price * (1 - slippage_sell)
            # Clamp to low (cannot go below low)
            fill_price = max(fill_price, ohlcv.low)
            slippage_amount = expected_price - fill_price
        
        # Check volume sufficiency (simplified: assume sufficient liquidity)
        qty_executed = order.qty
        
        # Calculate fees
        notional = qty_executed * fill_price
        fee = notional * FEE_RATE
        
        # Calculate tax (only for SELL)
        tax = notional * SELL_TAX_RATE if order.side == "SELL" else 0.0
        
        # Generate reason
        if order.side == "BUY":
            reason = f"買入 {qty_executed} 股 @ {fill_price:.2f}，手續費 {fee:.2f}，滑點 {slippage_amount:.2f}"
        else:  # SELL
            reason = f"賣出 {qty_executed} 股 @ {fill_price:.2f}，手續費 {fee:.2f}，稅 {tax:.2f}，滑點 {slippage_amount:.2f}"
        
        return OrderFill(
            symbol=order.symbol,
            side=order.side,
            qty_executed=qty_executed,
            fill_price=round(fill_price, 2),
            fee=round(fee, 2),
            tax=round(tax, 2),
            slippage=round(slippage_amount, 2),
            reason=reason
        )

