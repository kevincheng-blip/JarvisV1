"""Flow Alpha Factor

This module implements the Flow Alpha factor, including:
- F_Flow_Net: Net flow strength
- F_Flow_Ecosystem: Ecosystem flow influence

Based on: structured_books/股神腦系統具體化設計_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase


class FlowFactor(FactorBase):
    """Flow Alpha Factor
    
    Computes flow-based alpha signals including:
    - flow_strength: Net flow strength (z-score)
    - ecosystem_influence: Ecosystem flow influence (z-score)
    
    Based on F_Flow_Net and F_Flow_Ecosystem concepts.
    
    Example:
        factor = FlowFactor()
        flow_score = factor.compute(df)
    """
    
    def __init__(self, lookback_window: int = 20):
        """Initialize Flow Factor
        
        Args:
            lookback_window: Window size for rolling statistics (default: 20)
        """
        super().__init__("flow_factor")
        self.lookback_window = lookback_window
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute flow factor values
        
        Args:
            df: DataFrame with columns:
                - close: Close price
                - volume: Trading volume
                - foreign_flow: Foreign investor net flow (optional)
                - ecosystem_flow: Ecosystem flow data (optional)
                - major_buy_volume: Major buy volume (optional)
                - major_sell_volume: Major sell volume (optional)
        
        Returns:
            pd.Series: Combined flow score (z-score standardized)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        # Compute flow strength (F_Flow_Net)
        flow_strength = self._compute_flow_strength(df)
        
        # Compute ecosystem influence (F_Flow_Ecosystem)
        ecosystem_influence = self._compute_ecosystem_influence(df)
        
        # Combine scores (weighted average)
        flow_score = (flow_strength * 0.6 + ecosystem_influence * 0.4)
        
        # Standardize
        flow_score = self.standardize(flow_score, window=self.lookback_window)
        
        # Fill NaN with 0
        flow_score = self.fillna(flow_score, fill_value=0.0)
        
        return flow_score
    
    def _compute_flow_strength(self, df: pd.DataFrame) -> pd.Series:
        """Compute net flow strength (F_Flow_Net)
        
        Args:
            df: DataFrame with flow data
        
        Returns:
            pd.Series: Flow strength scores
        """
        if 'volume' not in df.columns:
            return pd.Series(0.0, index=df.index)
        
        # Base flow strength from volume momentum
        volume = df['volume'].fillna(0)
        
        # Calculate volume change rate
        volume_change = volume.pct_change().fillna(0)
        
        # Calculate price-volume relationship
        if 'close' in df.columns:
            price_change = df['close'].pct_change().fillna(0)
            # Positive correlation: price up + volume up = strong flow
            flow_strength = volume_change * np.sign(price_change)
        else:
            flow_strength = volume_change
        
        # Include foreign flow if available
        if 'foreign_flow' in df.columns:
            foreign_flow = df['foreign_flow'].fillna(0)
            foreign_flow_normalized = self.standardize(foreign_flow, window=self.lookback_window)
            flow_strength = flow_strength + foreign_flow_normalized * 0.3
        
        # Include major order imbalance if available
        if 'major_buy_volume' in df.columns and 'major_sell_volume' in df.columns:
            major_buy = df['major_buy_volume'].fillna(0)
            major_sell = df['major_sell_volume'].fillna(0)
            total_major = major_buy + major_sell
            
            # Calculate MOI (Major Order Imbalance)
            moi = pd.Series(0.0, index=df.index)
            mask = total_major > 0
            moi[mask] = (major_buy[mask] - major_sell[mask]) / total_major[mask]
            
            moi_normalized = self.standardize(moi, window=self.lookback_window)
            flow_strength = flow_strength + moi_normalized * 0.2
        
        return flow_strength
    
    def _compute_ecosystem_influence(self, df: pd.DataFrame) -> pd.Series:
        """Compute ecosystem flow influence (F_Flow_Ecosystem)
        
        Args:
            df: DataFrame with ecosystem flow data
        
        Returns:
            pd.Series: Ecosystem influence scores
        """
        if 'ecosystem_flow' in df.columns:
            ecosystem_flow = df['ecosystem_flow'].fillna(0)
            ecosystem_score = self.standardize(ecosystem_flow, window=self.lookback_window)
        else:
            # Fallback: use volume as proxy
            if 'volume' in df.columns:
                volume = df['volume'].fillna(0)
                # Calculate relative volume strength
                volume_ma = volume.rolling(window=self.lookback_window, min_periods=1).mean()
                ecosystem_score = (volume - volume_ma) / (volume_ma + 1e-6)  # Avoid division by zero
                ecosystem_score = self.standardize(ecosystem_score, window=self.lookback_window)
            else:
                ecosystem_score = pd.Series(0.0, index=df.index)
        
        return ecosystem_score.fillna(0)

