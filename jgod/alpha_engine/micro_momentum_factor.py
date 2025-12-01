"""Micro-Momentum Alpha Factor

This module is a placeholder for Micro-Momentum Alpha factor.
Will be implemented when Path A provides intraday data support.

Based on: structured_books/Path A 歷史回測撈取資料＋分析_AI知識庫版_v1_CORRECTED.md
"""

from __future__ import annotations

from typing import Optional
import pandas as pd

from jgod.alpha_engine.factor_base import FactorBase


class MicroMomentumFactor(FactorBase):
    """Micro-Momentum Alpha Factor (Placeholder)
    
    This factor will be implemented when Path A provides intraday data support.
    For now, it returns neutral scores.
    
    Future implementation will analyze:
    - Intraday momentum patterns
    - Microstructure signals
    - High-frequency flow dynamics
    
    Example:
        factor = MicroMomentumFactor()
        # Currently returns all zeros
        momentum_score = factor.compute(df)
    """
    
    def __init__(self):
        """Initialize Micro-Momentum Factor (placeholder)"""
        super().__init__("micro_momentum_factor")
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute micro-momentum factor values (placeholder)
        
        Currently returns neutral scores (all zeros) until Path A intraday data is available.
        
        Args:
            df: DataFrame with intraday data (when implemented)
        
        Returns:
            pd.Series: Neutral scores (all zeros) for now
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        # Placeholder: return neutral scores
        return pd.Series(0.0, index=df.index)

