"""Value / Quality Alpha Factor

This module implements the Value/Quality Alpha factor using fundamental metrics:
- ROA (Return on Assets)
- GP/A (Gross Profit to Assets)
- B/M (Book-to-Market)
- Debt ratio (financial stability)

Based on value and quality investing principles.
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np

from jgod.alpha_engine.factor_base import FactorBase


class ValueQualityFactor(FactorBase):
    """Value/Quality Alpha Factor
    
    Computes fundamental-based alpha signals using value and quality metrics.
    These metrics are expected to be provided by Path A data pipeline.
    
    Example:
        factor = ValueQualityFactor()
        value_quality_score = factor.compute(df)
    """
    
    def __init__(self, lookback_window: int = 252):
        """Initialize Value/Quality Factor
        
        Args:
            lookback_window: Window size for rolling statistics (default: 252 for annual)
        """
        super().__init__("value_quality_factor")
        self.lookback_window = lookback_window
    
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute value/quality factor values
        
        Args:
            df: DataFrame with columns:
                - roa: Return on Assets (optional)
                - gpa: Gross Profit to Assets (optional)
                - bm: Book-to-Market ratio (optional)
                - debt_ratio: Debt ratio (optional)
                - close: Close price (for fallback calculations)
        
        Returns:
            pd.Series: Value/Quality score (z-score standardized)
        """
        if df.empty:
            return pd.Series(dtype=float)
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                df.index = pd.to_datetime(df.index)
        
        quality_scores = []
        
        # 1. ROA (Return on Assets) - profitability measure
        roa_score = self._compute_roa_score(df)
        if roa_score is not None:
            quality_scores.append(roa_score)
        
        # 2. GP/A (Gross Profit to Assets) - efficiency measure
        gpa_score = self._compute_gpa_score(df)
        if gpa_score is not None:
            quality_scores.append(gpa_score)
        
        # 3. B/M (Book-to-Market) - value measure
        bm_score = self._compute_bm_score(df)
        if bm_score is not None:
            quality_scores.append(bm_score)
        
        # 4. Debt ratio - financial stability measure
        debt_score = self._compute_debt_score(df)
        if debt_score is not None:
            quality_scores.append(debt_score)
        
        if not quality_scores:
            # No fundamental data available - return neutral score
            return pd.Series(0.0, index=df.index)
        
        # Combine scores (equal weight for now)
        combined_score = pd.Series(0.0, index=df.index)
        for score in quality_scores:
            combined_score = combined_score + score.fillna(0)
        
        combined_score = combined_score / len(quality_scores)
        
        # Standardize
        combined_score = self.standardize(combined_score, window=self.lookback_window)
        
        # Fill NaN with 0
        combined_score = self.fillna(combined_score, fill_value=0.0)
        
        return combined_score
    
    def _compute_roa_score(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute ROA (Return on Assets) score
        
        Higher ROA = better profitability = higher score
        
        Args:
            df: DataFrame with ROA data
        
        Returns:
            pd.Series: ROA score, or None if data unavailable
        """
        if 'roa' not in df.columns:
            return None
        
        roa = df['roa'].fillna(0)
        
        # Standardize ROA
        roa_score = self.standardize(roa, window=self.lookback_window)
        
        return roa_score
    
    def _compute_gpa_score(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute GP/A (Gross Profit to Assets) score
        
        Higher GP/A = better efficiency = higher score
        
        Args:
            df: DataFrame with GP/A data
        
        Returns:
            pd.Series: GP/A score, or None if data unavailable
        """
        if 'gpa' not in df.columns:
            return None
        
        gpa = df['gpa'].fillna(0)
        
        # Standardize GP/A
        gpa_score = self.standardize(gpa, window=self.lookback_window)
        
        return gpa_score
    
    def _compute_bm_score(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute B/M (Book-to-Market) score
        
        Higher B/M = more undervalued = higher score (value factor)
        
        Args:
            df: DataFrame with B/M data
        
        Returns:
            pd.Series: B/M score, or None if data unavailable
        """
        if 'bm' not in df.columns:
            return None
        
        bm = df['bm'].fillna(0)
        
        # Standardize B/M
        bm_score = self.standardize(bm, window=self.lookback_window)
        
        return bm_score
    
    def _compute_debt_score(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Compute debt ratio score
        
        Lower debt ratio = better financial stability = higher score
        
        Args:
            df: DataFrame with debt ratio data
        
        Returns:
            pd.Series: Debt score (inverted, so higher = better), or None if data unavailable
        """
        if 'debt_ratio' not in df.columns:
            return None
        
        debt_ratio = df['debt_ratio'].fillna(0)
        
        # Invert debt ratio (lower is better)
        # Use 1 - normalized_debt_ratio to make higher = better
        debt_normalized = debt_ratio.clip(0, 1)  # Ensure [0, 1] range
        debt_score = 1 - debt_normalized
        
        # Standardize
        debt_score = self.standardize(debt_score, window=self.lookback_window)
        
        return debt_score

