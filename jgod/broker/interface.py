"""
Broker Adapter Interface: Abstract broker layer

v0.6.11-A11: Decouples execution from broker implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class OrderRequest:
    """Order request structure."""
    symbol: str
    side: str  # "BUY", "SELL", "HOLD"
    qty: int
    price: Optional[float] = None  # Optional limit price
    order_type: str = "MARKET"  # "MARKET", "LIMIT"
    reason: str = ""


@dataclass
class Fill:
    """Fill structure."""
    symbol: str
    side: str
    qty: int
    price: float
    timestamp: str
    order_id: Optional[str] = None


@dataclass
class Position:
    """Position structure."""
    symbol: str
    qty: int
    avg_cost: float
    market_value: float


@dataclass
class AccountBalance:
    """Account balance structure."""
    cash: float
    equity: float
    margin_used: float = 0.0


class BrokerAdapterInterface(ABC):
    """
    Abstract broker adapter interface.
    
    v0.6.11-A11: Decouples execution from broker implementation.
    Paper Trading, IB, and other brokers implement this interface.
    """
    
    @abstractmethod
    def place_order(self, order: OrderRequest) -> str:
        """
        Place an order.
        
        Args:
            order: OrderRequest
            
        Returns:
            Order ID (string)
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get current positions.
        
        Returns:
            List of Position objects
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> AccountBalance:
        """
        Get account balance.
        
        Returns:
            AccountBalance object
        """
        pass
    
    @abstractmethod
    def subscribe_fills(self, callback: Callable[[Fill], None]) -> None:
        """
        Subscribe to fill events.
        
        Args:
            callback: Callback function that receives Fill objects
        """
        pass

