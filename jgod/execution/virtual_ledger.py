"""
Virtual Ledger: Position tracking and P&L calculation

Implements a minimal but correct ledger for execution simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
import uuid

# Taiwan equities typical fees
FEE_RATE = 0.001425  # 0.1425% commission
SELL_TAX_RATE = 0.003  # 0.3% transaction tax on sells


@dataclass
class PositionState:
    """Position state for a single symbol."""
    symbol: str
    qty: int = 0
    avg_cost: float = 0.0
    
    def market_value(self, price: float) -> float:
        """Calculate market value of position."""
        return self.qty * price
    
    def unrealized_pnl(self, price: float) -> float:
        """Calculate unrealized P&L."""
        if self.qty == 0:
            return 0.0
        return (price - self.avg_cost) * self.qty


@dataclass
class VirtualLedger:
    """Virtual ledger for execution simulation."""
    symbol: str
    cash: float
    positions: Dict[str, PositionState] = field(default_factory=dict)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    nav: float = 0.0  # cash + market value
    last_price: Dict[str, float] = field(default_factory=dict)
    updated_at: str = ""
    
    def __post_init__(self):
        """Initialize after creation."""
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
        if self.symbol not in self.positions:
            self.positions[self.symbol] = PositionState(symbol=self.symbol)
        # Initialize NAV
        self._update_nav()
    
    def _update_nav(self):
        """Update NAV from cash and positions."""
        market_value = sum(
            pos.market_value(self.last_price.get(pos.symbol, 0.0))
            for pos in self.positions.values()
        )
        self.nav = self.cash + market_value
        
        # Update unrealized P&L
        self.unrealized_pnl = sum(
            pos.unrealized_pnl(self.last_price.get(pos.symbol, 0.0))
            for pos in self.positions.values()
        )
    
    def mark_to_market(self, symbol: str, price: float):
        """Mark position to market price."""
        if price < 0:
            raise ValueError(f"Price must be non-negative, got {price}")
        
        self.last_price[symbol] = price
        
        # Ensure position exists
        if symbol not in self.positions:
            self.positions[symbol] = PositionState(symbol=symbol)
        
        self._update_nav()
        self.updated_at = datetime.now().isoformat()
    
    def buy(self, symbol: str, qty: int, price: float, fee_rate: float = FEE_RATE) -> Dict[str, any]:
        """
        Buy shares.
        
        Returns:
            dict with 'success', 'qty_executed', 'fee', 'message'
        """
        if qty <= 0:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "message": f"買入數量必須 > 0，收到 {qty}"
            }
        
        if price <= 0:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "message": f"價格必須 > 0，收到 {price}"
            }
        
        notional = qty * price
        fee = notional * fee_rate
        total_cost = notional + fee
        
        # Check cash sufficiency
        if self.cash < total_cost:
            max_qty = int((self.cash / (price * (1 + fee_rate))) - 1)
            if max_qty < 1:
                return {
                    "success": False,
                    "qty_executed": 0,
                    "fee": 0.0,
                    "message": f"現金不足：需要 {total_cost:.2f}，可用 {self.cash:.2f}"
                }
            qty = max_qty
            notional = qty * price
            fee = notional * fee_rate
            total_cost = notional + fee
        
        # Update cash
        self.cash -= total_cost
        
        # Update position (weighted average cost)
        if symbol not in self.positions:
            self.positions[symbol] = PositionState(symbol=symbol)
        
        pos = self.positions[symbol]
        old_qty = pos.qty
        old_avg_cost = pos.avg_cost
        
        new_qty = old_qty + qty
        if new_qty > 0:
            pos.avg_cost = (old_qty * old_avg_cost + notional) / new_qty
        pos.qty = new_qty
        
        # Mark to market
        self.mark_to_market(symbol, price)
        
        return {
            "success": True,
            "qty_executed": qty,
            "fee": fee,
            "message": f"買入 {qty} 股 @ {price:.2f}，手續費 {fee:.2f}"
        }
    
    def sell(self, symbol: str, qty: int, price: float, fee_rate: float = FEE_RATE, tax_rate: float = SELL_TAX_RATE) -> Dict[str, any]:
        """
        Sell shares.
        
        Returns:
            dict with 'success', 'qty_executed', 'fee', 'tax', 'realized_pnl', 'message'
        """
        if qty <= 0:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "tax": 0.0,
                "realized_pnl": 0.0,
                "message": f"賣出數量必須 > 0，收到 {qty}"
            }
        
        if price <= 0:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "tax": 0.0,
                "realized_pnl": 0.0,
                "message": f"價格必須 > 0，收到 {price}"
            }
        
        # Check position
        if symbol not in self.positions:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "tax": 0.0,
                "realized_pnl": 0.0,
                "message": f"無 {symbol} 持倉"
            }
        
        pos = self.positions[symbol]
        available_qty = pos.qty
        
        if available_qty <= 0:
            return {
                "success": False,
                "qty_executed": 0,
                "fee": 0.0,
                "tax": 0.0,
                "realized_pnl": 0.0,
                "message": f"持倉不足：需要 {qty}，可用 {available_qty}"
            }
        
        # Clamp qty to available
        qty_executed = min(qty, available_qty)
        
        notional = qty_executed * price
        fee = notional * fee_rate
        tax = notional * tax_rate
        net_proceeds = notional - fee - tax
        
        # Calculate realized P&L
        avg_cost = pos.avg_cost
        realized_pnl = (price - avg_cost) * qty_executed - fee - tax
        
        # Update cash
        self.cash += net_proceeds
        
        # Update realized P&L
        self.realized_pnl += realized_pnl
        
        # Update position
        pos.qty -= qty_executed
        if pos.qty == 0:
            pos.avg_cost = 0.0
        
        # Mark to market
        self.mark_to_market(symbol, price)
        
        return {
            "success": True,
            "qty_executed": qty_executed,
            "fee": fee,
            "tax": tax,
            "realized_pnl": realized_pnl,
            "message": f"賣出 {qty_executed} 股 @ {price:.2f}，手續費 {fee:.2f}，稅 {tax:.2f}，已實現損益 {realized_pnl:.2f}"
        }
    
    def apply_fill(self, fill) -> Dict[str, any]:
        """
        Apply order fill to ledger.
        
        Args:
            fill: OrderFill object (from fill_engine)
            
        Returns:
            dict with 'success', 'message'
        """
        if fill.side == "HOLD":
            return {
                "success": True,
                "message": "HOLD 訂單，無需執行"
            }
        
        if fill.side == "BUY":
            return self.buy(fill.symbol, fill.qty_executed, fill.fill_price, fill.fee)
        else:  # SELL
            return self.sell(fill.symbol, fill.qty_executed, fill.fill_price, fill.fee, fill.tax)
    
    def snapshot(self, symbol: str) -> Dict:
        """Create snapshot dict for storage/API."""
        pos = self.positions.get(symbol, PositionState(symbol=symbol))
        
        return {
            "symbol": symbol,
            "cash": self.cash,
            "position": {
                "qty": pos.qty,
                "avg_cost": pos.avg_cost,
                "market_value": pos.market_value(self.last_price.get(symbol, 0.0)),
                "unrealized_pnl": pos.unrealized_pnl(self.last_price.get(symbol, 0.0)),
            },
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "nav": self.nav,
            "last_price": self.last_price.get(symbol, 0.0),
            "updated_at": self.updated_at,
        }

