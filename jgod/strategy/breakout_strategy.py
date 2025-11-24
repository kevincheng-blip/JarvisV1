"""
突破策略：當價格突破移動平均線時產生買入訊號
"""
from typing import Optional
from datetime import datetime
import pandas as pd

from .base_strategy import BaseStrategy, Signal, SignalType


class BreakoutStrategy(BaseStrategy):
    """
    突破策略
    
    邏輯：
    - 當收盤價突破 MA20 且 RSI < 70 時，產生買入訊號
    - 當收盤價跌破 MA20 或 RSI > 80 時，產生賣出訊號
    """
    
    def __init__(self, ma_period: int = 20, rsi_period: int = 14):
        """
        初始化突破策略
        
        Args:
            ma_period: 移動平均線週期（預設：20）
            rsi_period: RSI 週期（預設：14）
        """
        super().__init__("突破策略")
        self.ma_period = ma_period
        self.rsi_period = rsi_period
    
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
            data: 歷史價格資料
            current_price: 當前價格
        
        Returns:
            交易訊號
        """
        if not self.validate_data(data):
            return None
        
        # 確保有必要的技術指標
        if f"ma{self.ma_period}" not in data.columns:
            from jgod.market.indicators import TechnicalIndicators
            data = TechnicalIndicators.add_all_indicators(data)
        
        if len(data) < self.ma_period:
            return None
        
        # 取得當前資料
        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else current
        
        price = current_price if current_price is not None else float(current["close"])
        ma = float(current.get(f"ma{self.ma_period}", price))
        prev_ma = float(previous.get(f"ma{self.ma_period}", ma))
        rsi = float(current.get("rsi", 50.0))
        
        # 判斷突破
        price_above_ma = price > ma
        prev_price_above_ma = float(previous["close"]) > prev_ma
        
        # 買入訊號：價格突破 MA 且 RSI 未過熱
        if price_above_ma and not prev_price_above_ma and rsi < 70:
            return Signal(
                signal_type=SignalType.BUY,
                symbol=symbol,
                timestamp=datetime.now(),
                price=price,
                confidence=min(0.8, (70 - rsi) / 70),
                reason=f"價格突破 MA{self.ma_period}，RSI={rsi:.1f}",
                metadata={"ma": ma, "rsi": rsi},
            )
        
        # 賣出訊號：價格跌破 MA 或 RSI 過熱
        if (not price_above_ma and prev_price_above_ma) or rsi > 80:
            return Signal(
                signal_type=SignalType.SELL,
                symbol=symbol,
                timestamp=datetime.now(),
                price=price,
                confidence=0.7 if rsi > 80 else 0.6,
                reason=f"價格跌破 MA{self.ma_period} 或 RSI 過熱（RSI={rsi:.1f}）",
                metadata={"ma": ma, "rsi": rsi},
            )
        
        return None

