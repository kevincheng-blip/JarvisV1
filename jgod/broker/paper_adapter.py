"""
Paper Trading Adapter: Mock broker for paper trading

v0.6.11-A11: First broker adapter implementation
Wraps VirtualLedger and FillEngine, conforms to BrokerAdapterInterface
"""

import logging
from typing import List, Callable, Optional
from datetime import datetime
import uuid

from jgod.broker.interface import (
    BrokerAdapterInterface,
    OrderRequest,
    Fill,
    Position,
    AccountBalance,
)
from jgod.execution.virtual_ledger import VirtualLedger
from jgod.execution.fill_engine import FillEngine
from jgod.data.market_data_service import MarketDataService, OHLCVSnapshot

logger = logging.getLogger(__name__)


class PaperTradingAdapter(BrokerAdapterInterface):
    """
    Paper Trading Adapter: Mock broker implementation.
    
    v0.6.11-A11: Wraps VirtualLedger and FillEngine.
    Does not expose FillEngine directly to OrderEngine.
    """
    
    def __init__(
        self,
        initial_cash: float = 1_000_000.0,
        use_mock_mdts: bool = False,
        state_path: Optional[Path] = None,
    ):
        """
        Initialize Paper Trading Adapter.
        
        v0.6.12-A12: Added ledger state persistence.
        
        Args:
            initial_cash: Initial cash balance
            use_mock_mdts: If True, use mock MDTS (for testing)
            state_path: Optional custom state path (default: data/execution/ledger_state.json)
        """
        from pathlib import Path
        import json
        
        # v0.6.12-A12: Load ledger state if exists
        if state_path is None:
            project_root = Path(__file__).resolve().parents[2]
            state_dir = project_root / "data" / "execution"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = state_dir / "ledger_state.json"
        
        self.state_path = state_path
        
        # Try to load saved ledger state
        ledger_state = self._load_ledger_state()
        if ledger_state:
            # Restore ledger from state
            self.ledger = VirtualLedger(symbol="PORTFOLIO", cash=ledger_state.get("cash", initial_cash))
            # Restore positions (simplified - would need full position restoration)
            logger.info(f"Restored ledger state: cash={self.ledger.cash}")
        else:
            self.ledger = VirtualLedger(symbol="PORTFOLIO", cash=initial_cash)
        
        self.fill_engine = FillEngine()
        self.mdts = MarketDataService(use_mock=use_mock_mdts)
        self._fill_callbacks: List[Callable[[Fill], None]] = []
        self._order_id_counter = 0
    
    def place_order(self, order: OrderRequest) -> str:
        """
        Place an order (paper trading).
        
        Args:
            order: OrderRequest
            
        Returns:
            Order ID
        """
        if order.side == "HOLD":
            return f"HOLD-{uuid.uuid4().hex[:8]}"
        
        # Generate order ID
        order_id = f"PAPER-{self._order_id_counter:06d}"
        self._order_id_counter += 1
        
        # Get current price from MDTS
        ohlcv = self.mdts.fetch_ohlcv(order.symbol, datetime.now().strftime("%Y-%m-%d"))
        if ohlcv is None:
            logger.warning(f"No OHLCV data for {order.symbol}, using order price or 0")
            price = order.price if order.price else 0.0
        else:
            price = ohlcv.close
        
        # Execute fill using FillEngine (internal, not exposed)
        fill = self.fill_engine.execute(
            order={
                "symbol": order.symbol,
                "side": order.side,
                "qty": order.qty,
                "price": price,
            },
            ohlcv=ohlcv,
        )
        
        # Apply fill to ledger
        self.ledger.apply_fill(fill)
        
        # Mark to market
        if ohlcv:
            self.ledger.mark_to_market(order.symbol, ohlcv.close)
        
        # v0.6.12-A12: Save ledger state after each fill
        self._save_ledger_state()
        
        # Create Fill object and notify callbacks
        fill_obj = Fill(
            symbol=order.symbol,
            side=order.side,
            qty=fill.get("qty", order.qty),
            price=fill.get("price", price),
            timestamp=datetime.now().isoformat(),
            order_id=order_id,
        )
        
        # Notify subscribers
        for callback in self._fill_callbacks:
            try:
                callback(fill_obj)
            except Exception as e:
                logger.error(f"Fill callback error: {e}", exc_info=True)
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order (paper trading - no-op for now).
        
        Args:
            order_id: Order ID
            
        Returns:
            True (paper trading always succeeds)
        """
        logger.info(f"Cancel order {order_id} (paper trading - no-op)")
        return True
    
    def get_positions(self) -> List[Position]:
        """
        Get current positions from ledger.
        
        Returns:
            List of Position objects
        """
        positions = []
        for symbol, pos in self.ledger.positions.items():
            if pos.qty != 0:
                # Get current price
                ohlcv = self.mdts.fetch_ohlcv(symbol, datetime.now().strftime("%Y-%m-%d"))
                market_price = ohlcv.close if ohlcv else pos.avg_cost
                
                positions.append(Position(
                    symbol=symbol,
                    qty=pos.qty,
                    avg_cost=pos.avg_cost,
                    market_value=pos.qty * market_price,
                ))
        return positions
    
    def get_account_balance(self) -> AccountBalance:
        """
        Get account balance from ledger.
        
        Returns:
            AccountBalance object
        """
        # Calculate total equity
        total_equity = self.ledger.cash
        for symbol, pos in self.ledger.positions.items():
            if pos.qty != 0:
                ohlcv = self.mdts.fetch_ohlcv(symbol, datetime.now().strftime("%Y-%m-%d"))
                market_price = ohlcv.close if ohlcv else pos.avg_cost
                total_equity += pos.qty * market_price
        
        return AccountBalance(
            cash=self.ledger.cash,
            equity=total_equity,
            margin_used=0.0,  # Paper trading no margin
        )
    
    def subscribe_fills(self, callback: Callable[[Fill], None]) -> None:
        """
        Subscribe to fill events.
        
        Args:
            callback: Callback function that receives Fill objects
        """
        self._fill_callbacks.append(callback)
        logger.debug(f"Added fill callback (total: {len(self._fill_callbacks)})")
    
    def _save_ledger_state(self) -> None:
        """Save ledger state to file."""
        state = {
            "cash": self.ledger.cash,
            "realized_pnl": self.ledger.realized_pnl,
            "unrealized_pnl": self.ledger.unrealized_pnl,
            "nav": self.ledger.nav,
            "positions": {
                symbol: {"qty": pos.qty, "avg_cost": pos.avg_cost}
                for symbol, pos in self.ledger.positions.items()
            },
            "updated_at": datetime.now().isoformat(),
        }
        
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ledger state: {e}", exc_info=True)
    
    def _load_ledger_state(self) -> Optional[Dict]:
        """Load ledger state from file."""
        if not self.state_path.exists():
            return None
        
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load ledger state: {e}", exc_info=True)
            return None

