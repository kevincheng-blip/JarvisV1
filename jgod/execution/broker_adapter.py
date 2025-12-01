"""Broker Adapter v1

券商介面實作，用於連接真實或模擬券商。

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md
- spec/JGOD_ExecutionEngine_Spec.md
"""

from __future__ import annotations

from typing import Protocol, Optional

from .execution_types import Order, Fill


class BrokerAdapter(Protocol):
    """券商介面（用於連接真實或模擬券商）"""
    
    def submit_order(self, order: Order) -> str:
        """提交訂單
        
        Args:
            order: 交易訂單
        
        Returns:
            訂單 ID
        """
        ...
    
    def check_order_status(self, order_id: str) -> str:
        """檢查訂單狀態
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            訂單狀態（"pending", "filled", "cancelled" 等）
        """
        ...
    
    def get_fill(self, order_id: str) -> Optional[Fill]:
        """取得成交記錄
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            成交記錄（如果已成交），否則返回 None
        """
        ...


class MockBrokerAdapter:
    """模擬券商介面（預設 100% 成交）
    
    用於回測和模擬環境，所有訂單都會立即 100% 成交。
    """
    
    def __init__(self):
        """初始化模擬券商"""
        self._orders: dict[str, Order] = {}
        self._fills: dict[str, Fill] = {}
    
    def submit_order(self, order: Order) -> str:
        """提交訂單（模擬環境中立即返回訂單 ID）
        
        Args:
            order: 交易訂單
        
        Returns:
            訂單 ID
        """
        self._orders[order.order_id] = order
        return order.order_id
    
    def check_order_status(self, order_id: str) -> str:
        """檢查訂單狀態
        
        在模擬環境中，所有訂單都視為已成交。
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            訂單狀態（總是返回 "filled"）
        """
        if order_id in self._fills:
            return "filled"
        elif order_id in self._orders:
            # 在模擬環境中，訂單被提交後即視為已成交
            return "filled"
        else:
            return "not_found"
    
    def get_fill(self, order_id: str) -> Optional[Fill]:
        """取得成交記錄
        
        Args:
            order_id: 訂單 ID
        
        Returns:
            成交記錄（如果存在），否則返回 None
        """
        return self._fills.get(order_id)
    
    def create_fill(self, order: Order, fill_price: float, slippage: float = 0.0) -> Fill:
        """建立成交記錄（供 ExecutionEngine 使用）
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
            slippage: 滑價金額
        
        Returns:
            Fill 物件
        """
        from .execution_types import Fill
        
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            filled_quantity=order.quantity,
            fill_price=fill_price,
            slippage=slippage,
        )
        
        self._fills[order.order_id] = fill
        return fill

