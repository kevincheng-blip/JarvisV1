"""Cost Model v1

交易成本模型實作，用於計算手續費和稅費。

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Protocol, Optional

from .execution_types import Order


class CostModel(Protocol):
    """交易成本模型介面"""
    
    def compute_commission(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算手續費
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            手續費金額
        """
        ...
    
    def compute_tax(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算稅費
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            稅費金額（賣出時才收取）
        """
        ...
    
    def compute_total_cost(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算總交易成本
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            總成本（手續費 + 稅費）
        """
        ...


class DefaultCostModel:
    """預設成本模型（台股）
    
    手續費：買賣皆收取，費率 0.1425%，最低 20 元
    證交稅：僅賣出時收取，費率 0.3%
    """
    
    def __init__(
        self,
        commission_rate: float = 0.001425,
        min_commission: float = 20.0,
        tax_rate: float = 0.003
    ):
        """初始化預設成本模型
        
        Args:
            commission_rate: 手續費率（預設 0.1425%，即 0.001425）
            min_commission: 最低手續費（預設 20 元）
            tax_rate: 證交稅率（預設 0.3%，即 0.003）
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.tax_rate = tax_rate
    
    def compute_commission(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算手續費
        
        公式：commission = max(trade_amount * commission_rate, min_commission)
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            手續費金額
        """
        trade_amount = order.quantity * fill_price
        commission = trade_amount * self.commission_rate
        return max(commission, self.min_commission)
    
    def compute_tax(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算稅費（僅賣出時收取）
        
        公式：tax = sell_amount * tax_rate
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            稅費金額（買入時返回 0）
        """
        if order.side != "SELL":
            return 0.0
        
        sell_amount = order.quantity * fill_price
        return sell_amount * self.tax_rate
    
    def compute_total_cost(
        self,
        order: Order,
        fill_price: float
    ) -> float:
        """計算總交易成本
        
        Args:
            order: 交易訂單
            fill_price: 成交價格
        
        Returns:
            總成本（手續費 + 稅費）
        """
        commission = self.compute_commission(order, fill_price)
        tax = self.compute_tax(order, fill_price)
        return commission + tax

