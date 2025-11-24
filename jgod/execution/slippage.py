"""
滑價模型：模擬實際交易中的滑價
"""
from typing import Optional
import random


class SlippageModel:
    """
    滑價模型
    
    功能：
    - 模擬市價單滑價
    - 根據交易量調整滑價
    """
    
    def __init__(
        self,
        base_slippage_percent: float = 0.001,  # 基礎滑價 0.1%
        volume_impact_factor: float = 0.0001,  # 交易量影響因子
    ):
        """
        初始化滑價模型
        
        Args:
            base_slippage_percent: 基礎滑價百分比
            volume_impact_factor: 交易量影響因子
        """
        self.base_slippage_percent = base_slippage_percent
        self.volume_impact_factor = volume_impact_factor
    
    def apply_slippage(
        self,
        price: float,
        side: str,
        quantity: int,
    ) -> float:
        """
        應用滑價
        
        Args:
            price: 原始價格
            side: 交易方向（"buy" 或 "sell"）
            quantity: 數量
        
        Returns:
            考慮滑價後的價格
        """
        # 計算滑價百分比（根據交易量）
        slippage_percent = self.base_slippage_percent + (
            quantity * self.volume_impact_factor
        )
        
        # 加入隨機波動
        random_factor = random.uniform(0.5, 1.5)
        slippage_percent *= random_factor
        
        # 買入時價格上漲，賣出時價格下跌
        if side == "buy":
            return price * (1 + slippage_percent)
        else:  # sell
            return price * (1 - slippage_percent)
    
    def estimate_slippage(
        self,
        price: float,
        side: str,
        quantity: int,
    ) -> float:
        """
        估算滑價（不實際應用）
        
        Args:
            price: 原始價格
            side: 交易方向
            quantity: 數量
        
        Returns:
            預估滑價金額
        """
        slippage_percent = self.base_slippage_percent + (
            quantity * self.volume_impact_factor
        )
        return price * slippage_percent

