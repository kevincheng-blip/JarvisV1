"""
策略基類：所有交易策略都應該繼承此類別
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd


class SignalType(Enum):
    """訊號類型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    """交易訊號"""
    signal_type: SignalType
    symbol: str
    timestamp: datetime
    price: float
    confidence: float  # 0.0-1.0
    reason: str
    metadata: Optional[Dict[str, Any]] = None


class BaseStrategy(ABC):
    """
    策略基類
    
    所有交易策略都應該繼承此類別並實作 generate_signal 方法
    """
    
    def __init__(self, name: str):
        """
        初始化策略
        
        Args:
            name: 策略名稱
        """
        self.name = name
    
    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        current_price: Optional[float] = None,
    ) -> Optional[Signal]:
        """
        產生交易訊號
        
        Args:
            symbol: 股票代號
            data: 歷史價格資料（包含技術指標）
            current_price: 當前價格（如果為 None 則使用資料最後一筆）
        
        Returns:
            交易訊號，如果沒有訊號則回傳 None
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        驗證資料是否足夠
        
        Args:
            data: 要驗證的資料
        
        Returns:
            True 表示資料足夠，False 表示不足
        """
        if data.empty:
            return False
        if len(data) < 20:  # 至少需要 20 筆資料
            return False
        if "close" not in data.columns:
            return False
        return True
    
    def get_current_price(self, data: pd.DataFrame) -> float:
        """
        從資料取得當前價格
        
        Args:
            data: 價格資料
        
        Returns:
            當前價格
        """
        if data.empty:
            return 0.0
        return float(data["close"].iloc[-1])

