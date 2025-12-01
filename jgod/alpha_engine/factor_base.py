"""Base Factor Class for J-GOD Alpha Engine

This module provides the FactorBase abstract class that all alpha factors must inherit from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
import numpy as np


class FactorBase(ABC):
    """Base class for all alpha factors
    
    All alpha factors in J-GOD must inherit from this class and implement
    the compute() method.
    
    Example:
        class MyFactor(FactorBase):
            def __init__(self):
                super().__init__("my_factor")
            
            def compute(self, df: pd.DataFrame) -> pd.Series:
                # Implement factor calculation
                return pd.Series(...)
    """
    
    def __init__(self, name: str):
        """Initialize factor
        
        Args:
            name: Factor name (e.g., "flow_factor", "divergence_factor")
        """
        self.name = name
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """Compute factor values for a single stock
        
        Args:
            df: DataFrame containing stock data with columns:
                - Required: date (datetime index), close, volume
                - Optional: open, high, low, adj_close, and other fields
                  (e.g., foreign_flow, ecosystem_flow, etc.)
        
        Returns:
            pd.Series with same index as df, containing factor values.
            Values should be standardized (z-score) or normalized.
            Missing values should be filled with 0.
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"{self.__class__.__name__}.compute() must be implemented")
    
    def standardize(self, series: pd.Series, window: Optional[int] = None) -> pd.Series:
        """Standardize a series to z-score
        
        Args:
            series: Input series to standardize
            window: Rolling window size for standardization. If None, uses entire series.
        
        Returns:
            Standardized series (z-scores)
        """
        if series.empty:
            return series
        
        # Fill NaN with 0
        series = series.fillna(0)
        
        if window is None or len(series) < window:
            # Use entire series for standardization
            mean = series.mean()
            std = series.std()
            if std == 0 or np.isnan(std):
                return pd.Series(0.0, index=series.index)
            return (series - mean) / std
        else:
            # Rolling z-score
            rolling_mean = series.rolling(window=window, min_periods=1).mean()
            rolling_std = series.rolling(window=window, min_periods=1).std()
            rolling_std = rolling_std.replace(0, np.nan).fillna(1.0)  # Avoid division by zero
            standardized = (series - rolling_mean) / rolling_std
            return standardized.fillna(0)
    
    def normalize(self, series: pd.Series, method: str = "minmax") -> pd.Series:
        """Normalize a series to [0, 1] or [-1, 1] range
        
        Args:
            series: Input series to normalize
            method: Normalization method ("minmax" for [0,1], "zscore" for z-score)
        
        Returns:
            Normalized series
        """
        if series.empty:
            return series
        
        series = series.fillna(0)
        
        if method == "minmax":
            min_val = series.min()
            max_val = series.max()
            if max_val == min_val:
                return pd.Series(0.5, index=series.index)
            return (series - min_val) / (max_val - min_val)
        else:
            return self.standardize(series)
    
    def fillna(self, series: pd.Series, fill_value: float = 0.0) -> pd.Series:
        """Fill missing values in series
        
        Args:
            series: Input series
            fill_value: Value to fill NaN with (default: 0.0)
        
        Returns:
            Series with NaN filled
        """
        return series.fillna(fill_value)

