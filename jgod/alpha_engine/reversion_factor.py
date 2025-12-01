"""Reversion Alpha Factor

This module implements the Reversion Alpha factor based on "萬物修復法則" (Everything Repair Rule).
Includes:
1. Overextension score (F_Overextension)
2. Reversion pressure (F_Reversion_Pressure)
3. Distance to equilibrium (F_Distance_to_Equilibrium)

Based on: structured_books/股市大自然萬物修復法則_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase


class ReversionFactor(FactorBase):
    """Reversion Alpha Factor
    
    Computes mean reversion signals based on the "萬物修復法則" principle.
    Detects when prices have moved too far from equilibrium and signals potential reversions.
    
    Example:
        factor = ReversionFactor()
        reversion_score = factor.compute(df)
    """
    
    def __init__(self, lookback_window: int = 20, ma_window: int = 20):
        """Initialize Reversion Factor
        
        Args:
            lookback_window: Window size for rolling statistics (default: 20)
            ma_window: Window size for moving average (equilibrium level, default: 20)
        """
        super().__init__("reversion_factor")
        self.lookback_window = lookback_window
        self.ma_window = ma_window
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute reversion factor values
        
        Args:
            df: DataFrame with columns:
                - close: Close price
                - high: High price (optional)
                - low: Low price (optional)
                - volume: Trading volume (optional)
        
        Returns:
            pd.Series: Reversion score (z-score standardized)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        if 'close' not in df.columns:
            return pd.Series(0.0, index=df.index)
        
        reversion_scores = []
        
        # 1. Overextension score (F_Overextension)
        overextension = self._compute_overextension(df)
        if overextension is not None:
            reversion_scores.append(overextension)
        
        # 2. Reversion pressure (F_Reversion_Pressure)
        reversion_pressure = self._compute_reversion_pressure(df)
        if reversion_pressure is not None:
            reversion_scores.append(reversion_pressure)
        
        # 3. Distance to equilibrium (F_Distance_to_Equilibrium)
        distance_to_eq = self._compute_distance_to_equilibrium(df)
        if distance_to_eq is not None:
            reversion_scores.append(distance_to_eq)
        
        if not reversion_scores:
            return pd.Series(0.0, index=df.index)
        
        # Combine scores (equal weight)
        combined_score = pd.Series(0.0, index=df.index)
        for score in reversion_scores:
            combined_score = combined_score + score.fillna(0)
        
        combined_score = combined_score / len(reversion_scores)
        
        # Standardize
        combined_score = self.standardize(combined_score, window=self.lookback_window)
        
        # Fill NaN with 0
        combined_score = self.fillna(combined_score, fill_value=0.0)
        
        return combined_score
    
    def _compute_overextension(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute overextension score
        
        Measures how far price has moved from its recent range.
        
        Args:
            df: DataFrame with price data
        
        Returns:
            pd.Series: Overextension score
        """
        price = df['close'].fillna(method='ffill')
        
        # Calculate rolling high and low
        if 'high' in df.columns and 'low' in df.columns:
            rolling_high = df['high'].rolling(window=self.ma_window, min_periods=1).max()
            rolling_low = df['low'].rolling(window=self.ma_window, min_periods=1).min()
        else:
            # Fallback: use close price
            rolling_high = price.rolling(window=self.ma_window, min_periods=1).max()
            rolling_low = price.rolling(window=self.ma_window, min_periods=1).min()
        
        # Calculate range
        price_range = rolling_high - rolling_low
        price_range = price_range.replace(0, np.nan).fillna(price.rolling(window=self.ma_window, min_periods=1).std())
        
        # Calculate distance from range center
        range_center = (rolling_high + rolling_low) / 2
        distance_from_center = price - range_center
        
        # Normalize by range (overextension ratio)
        overextension = distance_from_center / (price_range + 1e-6)
        
        # High positive = overextended upward (potential downward reversion)
        # High negative = overextended downward (potential upward reversion)
        return overextension
    
    def _compute_reversion_pressure(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute reversion pressure
        
        Measures the pressure for price to revert based on recent momentum and volatility.
        
        Args:
            df: DataFrame with price data
        
        Returns:
            pd.Series: Reversion pressure score
        """
        price = df['close'].fillna(method='ffill')
        
        # Calculate recent momentum
        trend_window = min(self.ma_window // 2, 10)
        returns = price.pct_change().fillna(0)
        momentum = returns.rolling(window=trend_window, min_periods=1).sum()
        
        # Calculate volatility
        volatility = returns.rolling(window=self.ma_window, min_periods=1).std()
        volatility = volatility.replace(0, np.nan).fillna(returns.std() if not returns.empty else 1.0)
        
        # Reversion pressure = momentum / volatility
        # High momentum relative to volatility = high reversion pressure
        reversion_pressure = momentum / (volatility + 1e-6)
        
        # Negative sign: if momentum is positive, pressure is negative (to revert down)
        return -reversion_pressure
    
    def _compute_distance_to_equilibrium(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute distance to equilibrium (e.g., 20MA)
        
        Measures how far price is from its moving average (equilibrium level).
        
        Args:
            df: DataFrame with price data
        
        Returns:
            pd.Series: Distance to equilibrium score
        """
        price = df['close'].fillna(method='ffill')
        
        # Calculate moving average (equilibrium)
        ma = price.rolling(window=self.ma_window, min_periods=1).mean()
        
        # Calculate distance
        distance = (price - ma) / (ma + 1e-6)  # Percentage distance
        
        # Calculate standard deviation for normalization
        distance_std = distance.rolling(window=self.lookback_window, min_periods=1).std()
        distance_std = distance_std.replace(0, np.nan).fillna(distance.std() if not distance.empty else 1.0)
        
        # Normalize
        normalized_distance = distance / (distance_std + 1e-6)
        
        return normalized_distance

