"""
Order Generation Engine

Generates order requests from Decision V3 results and current ledger state.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import math

from jgod.decision_v3.models import DecisionV3Result
from jgod.execution.virtual_ledger import VirtualLedger, FEE_RATE


OrderSide = Literal["BUY", "SELL", "HOLD"]


@dataclass
class OrderRequest:
    """Order request generated from decision and ledger."""
    symbol: str
    side: OrderSide
    qty: int
    reason: str  # Traditional Chinese, 1-2 lines
    target_position_scale: float
    current_position_scale: float


class OrderGenerationEngine:
    """Engine for generating order requests from decisions."""
    
    @staticmethod
    def generate_orders(
        decision: DecisionV3Result,
        ledger: VirtualLedger,
        price: float,
        lot_size: int = 1
    ) -> OrderRequest:
        """
        Generate order request from decision and ledger.
        
        Args:
            decision: Decision V3 result
            ledger: Current ledger state
            price: Current market price
            lot_size: Minimum lot size (default 1 for Taiwan equities)
            
        Returns:
            OrderRequest
        """
        symbol = decision.symbol
        target_scale = decision.risk_plan.position_scale
        
        # Calculate current position scale
        nav = ledger.nav
        if nav <= 0:
            return OrderRequest(
                symbol=symbol,
                side="HOLD",
                qty=0,
                reason="NAV <= 0，無法計算目標倉位",
                target_position_scale=target_scale,
                current_position_scale=0.0
            )
        
        # Get current position
        pos = ledger.positions.get(symbol, None)
        current_qty = pos.qty if pos else 0
        current_value = current_qty * price
        current_scale = current_value / nav if nav > 0 else 0.0
        
        # Calculate target value
        target_value = nav * target_scale
        delta_value = target_value - current_value
        
        # Determine order side and qty
        if abs(delta_value) < price * 0.01:  # Less than 1% of one share
            return OrderRequest(
                symbol=symbol,
                side="HOLD",
                qty=0,
                reason=f"目標倉位比例 {target_scale:.2%}，當前 {current_scale:.2%}，差異過小",
                target_position_scale=target_scale,
                current_position_scale=current_scale
            )
        
        # Calculate qty needed
        qty = int(math.floor(abs(delta_value) / price))
        
        # Round to lot_size
        qty = (qty // lot_size) * lot_size
        
        if qty < lot_size:
            return OrderRequest(
                symbol=symbol,
                side="HOLD",
                qty=0,
                reason=f"目標倉位比例 {target_scale:.2%}，當前 {current_scale:.2%}，所需數量 < {lot_size} 股",
                target_position_scale=target_scale,
                current_position_scale=current_scale
            )
        
        # Check cash sufficiency for BUY
        if delta_value > 0:  # BUY
            max_affordable_qty = int((ledger.cash / (price * (1 + FEE_RATE))) // lot_size) * lot_size
            if max_affordable_qty < lot_size:
                return OrderRequest(
                    symbol=symbol,
                    side="HOLD",
                    qty=0,
                    reason=f"現金不足：目標倉位比例 {target_scale:.2%}，但可用現金僅 {ledger.cash:.2f}",
                    target_position_scale=target_scale,
                    current_position_scale=current_scale
                )
            qty = min(qty, max_affordable_qty)
            side = "BUY"
            reason = f"目標倉位比例 {target_scale:.2%}，當前 {current_scale:.2%}，買入 {qty} 股以達到目標"
        else:  # SELL
            qty = min(qty, current_qty)  # Cannot sell more than owned
            if qty < lot_size:
                return OrderRequest(
                    symbol=symbol,
                    side="HOLD",
                    qty=0,
                    reason=f"目標倉位比例 {target_scale:.2%}，當前 {current_scale:.2%}，但可賣數量 < {lot_size} 股",
                    target_position_scale=target_scale,
                    current_position_scale=current_scale
                )
            side = "SELL"
            reason = f"目標倉位比例 {target_scale:.2%}，當前 {current_scale:.2%}，賣出 {qty} 股以達到目標"
        
        return OrderRequest(
            symbol=symbol,
            side=side,
            qty=qty,
            reason=reason,
            target_position_scale=target_scale,
            current_position_scale=current_scale
        )

