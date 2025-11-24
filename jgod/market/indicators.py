"""
技術指標計算器：計算 MA、RSI、MACD 等技術指標
"""
from typing import Optional
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """
    技術指標計算器
    
    功能：
    - 移動平均線（MA5, MA10, MA20）
    - RSI（相對強弱指標）
    - MACD（指數平滑異同移動平均線）
    """
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        """
        計算移動平均線
        
        Args:
            df: 價格資料 DataFrame
            period: 週期（例如：5, 10, 20）
            column: 要計算的欄位（預設：close）
        
        Returns:
            移動平均線 Series
        """
        if column not in df.columns:
            return pd.Series(dtype=float)
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        """
        計算 RSI（相對強弱指標）
        
        Args:
            df: 價格資料 DataFrame
            period: 週期（預設：14）
            column: 要計算的欄位（預設：close）
        
        Returns:
            RSI 值 Series（0-100）
        """
        if column not in df.columns:
            return pd.Series(dtype=float)
        
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close",
    ) -> pd.DataFrame:
        """
        計算 MACD
        
        Args:
            df: 價格資料 DataFrame
            fast_period: 快線週期（預設：12）
            slow_period: 慢線週期（預設：26）
            signal_period: 訊號線週期（預設：9）
            column: 要計算的欄位（預設：close）
        
        Returns:
            包含 MACD、Signal、Histogram 的 DataFrame
        """
        if column not in df.columns:
            return pd.DataFrame()
        
        ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        result = pd.DataFrame({
            "macd": macd,
            "signal": signal,
            "histogram": histogram,
        })
        
        return result
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        為 DataFrame 加入所有常用指標
        
        Args:
            df: 價格資料 DataFrame
        
        Returns:
            加入指標後的 DataFrame
        """
        result = df.copy()
        
        if "close" not in result.columns:
            return result
        
        # 移動平均線
        result["ma5"] = TechnicalIndicators.calculate_ma(result, 5)
        result["ma10"] = TechnicalIndicators.calculate_ma(result, 10)
        result["ma20"] = TechnicalIndicators.calculate_ma(result, 20)
        
        # RSI
        result["rsi"] = TechnicalIndicators.calculate_rsi(result, 14)
        
        # MACD
        macd_data = TechnicalIndicators.calculate_macd(result)
        if not macd_data.empty:
            result["macd"] = macd_data["macd"]
            result["macd_signal"] = macd_data["signal"]
            result["macd_histogram"] = macd_data["histogram"]
        
        return result

