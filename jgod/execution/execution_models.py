"""Execution Models v1

滑價模型實作，用於計算考慮滑價後的成交價格。

Reference:
- docs/JGOD_EXECUTION_ENGINE_STANDARD_v1.md
"""

from __future__ import annotations

from typing import Protocol, Optional, Dict
from abc import ABC, abstractmethod

from .execution_types import Order


class ExecutionModel(Protocol):
    """滑價模型介面"""
    
    def apply_slippage(
        self,
        order: Order,
        market_price: float,
        market_data: Optional[Dict[str, any]] = None
    ) -> float:
        """計算考慮滑價後的成交價格
        
        Args:
            order: 交易訂單
            market_price: 市場價格
            market_data: 市場數據（成交量等，可選）
        
        Returns:
            考慮滑價後的成交價格
        """
        ...


class FixedSlippageModel:
    """固定滑價模型
    
    固定金額的滑價，不考慮市場條件。
    
    公式：fill_price = order_price + fixed_slippage * direction
    """
    
    def __init__(self, slippage: float = 0.1):
        """初始化固定滑價模型
        
        Args:
            slippage: 固定滑價金額（元）
        """
        self.slippage = slippage
    
    def apply_slippage(
        self,
        order: Order,
        market_price: float,
        market_data: Optional[Dict[str, any]] = None
    ) -> float:
        """計算考慮滑價後的成交價格
        
        Args:
            order: 交易訂單
            market_price: 市場價格
            market_data: 市場數據（未使用）
        
        Returns:
            考慮滑價後的成交價格
        """
        direction = 1.0 if order.side == "BUY" else -1.0
        return market_price + (self.slippage * direction)


class PercentageSlippageModel:
    """百分比滑價模型
    
    按訂單價格的百分比計算滑價。
    
    公式：fill_price = order_price * (1 + slippage_pct * direction)
    """
    
    def __init__(self, slippage_pct: float = 0.001):
        """初始化百分比滑價模型
        
        Args:
            slippage_pct: 滑價百分比（例如：0.001 表示 0.1%）
        """
        self.slippage_pct = slippage_pct
    
    def apply_slippage(
        self,
        order: Order,
        market_price: float,
        market_data: Optional[Dict[str, any]] = None
    ) -> float:
        """計算考慮滑價後的成交價格
        
        Args:
            order: 交易訂單
            market_price: 市場價格
            market_data: 市場數據（未使用）
        
        Returns:
            考慮滑價後的成交價格
        """
        direction = 1.0 if order.side == "BUY" else -1.0
        return market_price * (1.0 + self.slippage_pct * direction)


class VolumeImpactSlippageModel:
    """成交量基礎滑價模型
    
    根據交易量與市場成交量的比例計算滑價。
    
    公式：
    volume_ratio = order_quantity / daily_volume
    slippage = base_slippage * (1 + impact_factor * volume_ratio^2)
    fill_price = order_price * (1 + slippage * direction)
    """
    
    def __init__(
        self,
        base_slippage: float = 0.001,
        impact_factor: float = 1.0
    ):
        """初始化成交量基礎滑價模型
        
        Args:
            base_slippage: 基礎滑價百分比（例如：0.001 表示 0.1%）
            impact_factor: 市場衝擊係數
        """
        self.base_slippage = base_slippage
        self.impact_factor = impact_factor
    
    def apply_slippage(
        self,
        order: Order,
        market_price: float,
        market_data: Optional[Dict[str, any]] = None
    ) -> float:
        """計算考慮滑價後的成交價格
        
        Args:
            order: 交易訂單
            market_price: 市場價格
            market_data: 市場數據，需包含 'daily_volume' 鍵
        
        Returns:
            考慮滑價後的成交價格
        
        Raises:
            ValueError: 如果 market_data 缺少 daily_volume
        """
        direction = 1.0 if order.side == "BUY" else -1.0
        
        if market_data is None or "daily_volume" not in market_data:
            # 如果沒有成交量資料，回退到基礎滑價
            slippage = self.base_slippage
        else:
            daily_volume = market_data["daily_volume"]
            if daily_volume <= 0:
                slippage = self.base_slippage
            else:
                volume_ratio = order.quantity / daily_volume
                slippage = self.base_slippage * (
                    1.0 + self.impact_factor * (volume_ratio ** 2)
                )
        
        return market_price * (1.0 + slippage * direction)

