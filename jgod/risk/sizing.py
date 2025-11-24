"""
部位大小計算器：根據風險計算適當的持倉大小
"""
from typing import Optional
from dataclasses import dataclass


@dataclass
class SizingParams:
    """部位大小計算參數"""
    account_size: float  # 帳戶大小
    risk_per_trade: float = 0.02  # 每筆交易風險比例（2%）
    stop_loss_percent: float = 0.05  # 停損百分比（5%）


class PositionSizer:
    """
    部位大小計算器
    
    功能：
    - 根據風險計算適當的持倉大小
    - 考慮停損點
    - 分散風險模型
    """
    
    def __init__(self, params: Optional[SizingParams] = None):
        """
        初始化部位大小計算器
        
        Args:
            params: 計算參數
        """
        self.params = params or SizingParams(account_size=1000000.0)
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        risk_amount: Optional[float] = None,
    ) -> int:
        """
        計算部位大小
        
        Args:
            entry_price: 進場價格
            stop_loss_price: 停損價格（如果為 None 則使用百分比）
            risk_amount: 風險金額（如果為 None 則使用風險比例）
        
        Returns:
            建議的持倉數量（股數）
        """
        # 計算風險金額
        if risk_amount is None:
            risk_amount = self.params.account_size * self.params.risk_per_trade
        
        # 計算停損價格
        if stop_loss_price is None:
            stop_loss_price = entry_price * (1 - self.params.stop_loss_percent)
        
        # 計算每股風險
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            return 0
        
        # 計算數量
        quantity = int(risk_amount / risk_per_share)
        
        return max(0, quantity)
    
    def calculate_position_size_by_percent(
        self,
        entry_price: float,
        position_percent: float,
    ) -> int:
        """
        根據持倉比例計算部位大小
        
        Args:
            entry_price: 進場價格
            position_percent: 持倉比例（例如：0.1 表示 10%）
        
        Returns:
            建議的持倉數量
        """
        position_value = self.params.account_size * position_percent
        quantity = int(position_value / entry_price)
        return max(0, quantity)
    
    def calculate_max_position_size(
        self,
        entry_price: float,
        max_position_percent: float = 0.20,
    ) -> int:
        """
        計算最大持倉大小（根據單一標的限制）
        
        Args:
            entry_price: 進場價格
            max_position_percent: 最大持倉比例（預設：20%）
        
        Returns:
            最大持倉數量
        """
        max_position_value = self.params.account_size * max_position_percent
        quantity = int(max_position_value / entry_price)
        return max(0, quantity)

