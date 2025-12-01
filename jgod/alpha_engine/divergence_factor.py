"""Divergence Alpha Factor

This module implements the Divergence Alpha factor, detecting divergences between:
1. Price trend vs volume trend
2. Price trend vs foreign flow
3. Price trend vs ecosystem flow
4. Price vs predicted target (placeholder for future)

Based on divergence analysis concepts from J-GOD knowledge base.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase


class DivergenceFactor(FactorBase):
    """Divergence Alpha Factor
    
    Detects divergences between price movements and various flow indicators.
    Divergence signals can indicate potential reversals or continuations.
    
    Example:
        factor = DivergenceFactor()
        divergence_score = factor.compute(df)
    """
    
    def __init__(self, lookback_window: int = 20, trend_window: int = 10):
        """Initialize Divergence Factor
        
        Args:
            lookback_window: Window size for rolling statistics (default: 20)
            trend_window: Window size for trend calculation (default: 10)
        """
        super().__init__("divergence_factor")
        self.lookback_window = lookback_window
        self.trend_window = trend_window
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute divergence factor values
        
        Args:
            df: DataFrame with columns:
                - close: Close price
                - volume: Trading volume
                - foreign_flow: Foreign investor net flow (optional)
                - ecosystem_flow: Ecosystem flow data (optional)
                - predicted_target: Predicted price target (optional, placeholder)
        
        Returns:
            pd.Series: Divergence score (z-score standardized)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        divergence_scores = []
        
        # 1. Price trend vs volume trend divergence
        price_volume_div = self._compute_price_volume_divergence(df)
        if price_volume_div is not None:
            divergence_scores.append(price_volume_div)
        
        # 2. Price trend vs foreign flow divergence
        price_foreign_div = self._compute_price_foreign_divergence(df)
        if price_foreign_div is not None:
            divergence_scores.append(price_foreign_div)
        
        # 3. Price trend vs ecosystem flow divergence
        price_ecosystem_div = self._compute_price_ecosystem_divergence(df)
        if price_ecosystem_div is not None:
            divergence_scores.append(price_ecosystem_div)
        
        # 4. Price vs predicted target divergence (placeholder)
        # price_target_div = self._compute_price_target_divergence(df)
        # if price_target_div is not None:
        #     divergence_scores.append(price_target_div)
        
        if not divergence_scores:
            return pd.Series(0.0, index=df.index)
        
        # Combine divergence scores (equal weight)
        combined_score = pd.Series(0.0, index=df.index)
        for score in divergence_scores:
            combined_score = combined_score + score.fillna(0)
        
        combined_score = combined_score / len(divergence_scores)
        
        # Standardize
        combined_score = self.standardize(combined_score, window=self.lookback_window)
        
        # Fill NaN with 0
        combined_score = self.fillna(combined_score, fill_value=0.0)
        
        return combined_score
    
    def _compute_price_volume_divergence(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute divergence between price trend and volume trend
        
        Args:
            df: DataFrame with price and volume data
        
        Returns:
            pd.Series: Divergence score, or None if insufficient data
        """
        if 'close' not in df.columns or 'volume' not in df.columns:
            return None
        
        # Calculate price trend (moving average of returns)
        price = df['close'].fillna(method='ffill')
        price_returns = price.pct_change().fillna(0)
        price_trend = price_returns.rolling(window=self.trend_window, min_periods=1).mean()
        
        # Calculate volume trend (moving average of volume change)
        volume = df['volume'].fillna(0)
        volume_returns = volume.pct_change().fillna(0)
        volume_trend = volume_returns.rolling(window=self.trend_window, min_periods=1).mean()
        
        # Divergence: when price trend and volume trend move in opposite directions
        # Positive divergence: price up but volume down (potential weakness)
        # Negative divergence: price down but volume up (potential strength)
        divergence = price_trend - volume_trend
        
        return divergence
    
    def _compute_price_foreign_divergence(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute divergence between price trend and foreign flow
        
        Args:
            df: DataFrame with price and foreign flow data
        
        Returns:
            pd.Series: Divergence score, or None if insufficient data
        """
        if 'close' not in df.columns or 'foreign_flow' not in df.columns:
            return None
        
        # Calculate price trend
        price = df['close'].fillna(method='ffill')
        price_returns = price.pct_change().fillna(0)
        price_trend = price_returns.rolling(window=self.trend_window, min_periods=1).mean()
        
        # Normalize foreign flow
        foreign_flow = df['foreign_flow'].fillna(0)
        foreign_flow_normalized = self.standardize(foreign_flow, window=self.lookback_window)
        
        # Calculate foreign flow trend
        foreign_flow_trend = foreign_flow_normalized.rolling(window=self.trend_window, min_periods=1).mean()
        
        # Divergence
        divergence = price_trend - foreign_flow_trend
        
        return divergence
    
    def _compute_price_ecosystem_divergence(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute divergence between price trend and ecosystem flow
        
        Args:
            df: DataFrame with price and ecosystem flow data
        
        Returns:
            pd.Series: Divergence score, or None if insufficient data
        """
        if 'close' not in df.columns:
            return None
        
        # Calculate price trend
        price = df['close'].fillna(method='ffill')
        price_returns = price.pct_change().fillna(0)
        price_trend = price_returns.rolling(window=self.trend_window, min_periods=1).mean()
        
        # Get ecosystem flow trend
        if 'ecosystem_flow' in df.columns:
            ecosystem_flow = df['ecosystem_flow'].fillna(0)
            ecosystem_flow_normalized = self.standardize(ecosystem_flow, window=self.lookback_window)
            ecosystem_trend = ecosystem_flow_normalized.rolling(window=self.trend_window, min_periods=1).mean()
        else:
            # Fallback: use volume as proxy
            if 'volume' in df.columns:
                volume = df['volume'].fillna(0)
                volume_normalized = self.standardize(volume, window=self.lookback_window)
                ecosystem_trend = volume_normalized.rolling(window=self.trend_window, min_periods=1).mean()
            else:
                return None
        
        # Divergence
        divergence = price_trend - ecosystem_trend
        
        return divergence

