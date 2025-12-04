"""
Live Data Feed for Path E

提供即時市場資料（K 線、價格等）。
v1 實作 MockLiveFeed，從歷史資料做 replay。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd

from jgod.path_e.live_types import LiveBar


class LiveDataFeed(ABC):
    """即時資料流抽象介面"""
    
    @abstractmethod
    def get_next_bar(self, symbol: str) -> Optional[LiveBar]:
        """取得下一個 bar"""
        ...
    
    @abstractmethod
    def has_next(self, symbol: str) -> bool:
        """是否還有資料"""
        ...
    
    @abstractmethod
    def reset(self) -> None:
        """重置到起始位置"""
        ...


class MockLiveFeed(LiveDataFeed):
    """
    Mock 即時資料流
    
    從歷史資料（DataFrame 或 CSV）做 replay，模擬即時資料流。
    """
    
    def __init__(
        self,
        price_data: pd.DataFrame,
        symbols: List[str],
    ):
        """
        初始化 MockLiveFeed
        
        Args:
            price_data: 歷史價格資料 DataFrame
                - index: date (pd.DatetimeIndex)
                - columns: MultiIndex (symbol, field) 或 wide format
                必備欄位: open, high, low, close, volume
            symbols: 標的列表
        """
        self.price_data = price_data.copy()
        self.symbols = symbols
        self.current_indices: Dict[str, int] = {symbol: 0 for symbol in symbols}
        self.dates = sorted(price_data.index.unique())
        
        # 確保資料格式正確
        self._validate_data()
    
    def _validate_data(self) -> None:
        """驗證資料格式"""
        if self.price_data.empty:
            raise ValueError("price_data is empty")
        if len(self.dates) == 0:
            raise ValueError("No dates found in price_data")
    
    def get_next_bar(self, symbol: str) -> Optional[LiveBar]:
        """
        取得下一個 bar
        
        Args:
            symbol: 標的代碼
        
        Returns:
            LiveBar 或 None（如果沒有更多資料）
        """
        if symbol not in self.symbols:
            return None
        
        idx = self.current_indices[symbol]
        if idx >= len(self.dates):
            return None
        
        current_date = self.dates[idx]
        
        # 從 price_data 提取該日期、該標的的資料
        try:
            if isinstance(self.price_data.columns, pd.MultiIndex):
                # MultiIndex columns: (symbol, field)
                open_price = self.price_data.loc[current_date, (symbol, "open")]
                high_price = self.price_data.loc[current_date, (symbol, "high")]
                low_price = self.price_data.loc[current_date, (symbol, "low")]
                close_price = self.price_data.loc[current_date, (symbol, "close")]
                volume = self.price_data.loc[current_date, (symbol, "volume")]
            else:
                # Wide format: columns like "2330_open", "2330_close", etc.
                open_price = self.price_data.loc[current_date, f"{symbol}_open"]
                high_price = self.price_data.loc[current_date, f"{symbol}_high"]
                low_price = self.price_data.loc[current_date, f"{symbol}_low"]
                close_price = self.price_data.loc[current_date, f"{symbol}_close"]
                volume = self.price_data.loc[current_date, f"{symbol}_volume"]
            
            bar = LiveBar(
                symbol=symbol,
                ts=pd.Timestamp(current_date),
                open=float(open_price),
                high=float(high_price),
                low=float(low_price),
                close=float(close_price),
                volume=float(volume),
            )
            
            # 移動到下一個日期
            self.current_indices[symbol] += 1
            
            return bar
        except (KeyError, IndexError) as e:
            # 該日期或標的沒有資料
            self.current_indices[symbol] += 1
            return None
    
    def get_latest_bars(self) -> Dict[str, LiveBar]:
        """
        取得所有標的的最新 bar（同一時間點）
        
        Returns:
            {symbol: LiveBar} 字典
        """
        latest_bars = {}
        for symbol in self.symbols:
            bar = self.get_next_bar(symbol)
            if bar is not None:
                latest_bars[symbol] = bar
        return latest_bars
    
    def has_next(self, symbol: str) -> bool:
        """是否還有資料"""
        if symbol not in self.symbols:
            return False
        return self.current_indices[symbol] < len(self.dates)
    
    def has_next_any(self) -> bool:
        """是否有任何標的還有資料"""
        return any(self.has_next(symbol) for symbol in self.symbols)
    
    def reset(self) -> None:
        """重置到起始位置"""
        self.current_indices = {symbol: 0 for symbol in self.symbols}

