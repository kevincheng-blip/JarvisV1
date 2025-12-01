"""Factor Exposure Schema

This module defines the data structure for representing factor exposures,
which describe how much a stock is exposed to various risk factors.

The exposure schema is independent of AlphaEngine implementation and uses
DataFrame as the interface to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


@dataclass
class FactorExposure:
    """Factor Exposure data structure
    
    Represents the exposure of a single stock to various risk factors
    on a specific date.
    
    Attributes:
        symbol: Stock symbol (e.g., "2330")
        date: Date of the exposure (pandas Timestamp)
        exposures: Dictionary mapping factor names to exposure values
                   Keys can include:
                   - "flow": Flow factor exposure
                   - "divergence": Divergence factor exposure
                   - "reversion": Reversion factor exposure
                   - "inertia": Inertia factor exposure
                   - "value_quality": Value/Quality factor exposure
                   - "beta": Market beta (optional)
                   - "size": Size factor (optional)
    
    Example:
        exposure = FactorExposure(
            symbol="2330",
            date=pd.Timestamp("2024-01-15"),
            exposures={
                "flow": 0.5,
                "divergence": -0.2,
                "reversion": 0.3,
                "inertia": 0.1,
                "value_quality": 0.0
            }
        )
    """
    symbol: str
    date: pd.Timestamp
    exposures: Dict[str, float]
    
    def get_exposure_vector(self, factor_names: List[str]) -> np.ndarray:
        """Get exposure as a numpy array in the order of factor_names
        
        Args:
            factor_names: Ordered list of factor names
        
        Returns:
            numpy array of exposure values in the same order as factor_names
        """
        return np.array([self.exposures.get(factor, 0.0) for factor in factor_names])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'symbol': self.symbol,
            'date': self.date,
            **{f'exposure_{k}': v for k, v in self.exposures.items()}
        }


def exposures_from_alpha_df(symbol: str, df: pd.DataFrame) -> List[FactorExposure]:
    """Convert AlphaEngine output DataFrame to list of FactorExposure objects
    
    This function takes the output from AlphaEngine.compute_all() and converts
    it into FactorExposure objects. It does NOT import AlphaEngine directly
    to avoid circular dependencies.
    
    Args:
        symbol: Stock symbol
        df: DataFrame from AlphaEngine.compute_all() with columns:
            - flow_score
            - divergence_score
            - reversion_score
            - inertia_score
            - value_quality_score
            - composite_alpha (optional, not used)
            Index should be datetime dates
    
    Returns:
        List of FactorExposure objects, one for each date in df
    
    Example:
        from jgod.alpha_engine import AlphaEngine
        
        engine = AlphaEngine()
        alpha_df = engine.compute_all(stock_df)
        
        exposures = exposures_from_alpha_df("2330", alpha_df)
    """
    if df.empty:
        return []
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df = df.set_index('date')
        else:
            df.index = pd.to_datetime(df.index)
    
    exposures_list = []
    
    # Factor name mapping (from alpha_df columns to exposure dict keys)
    factor_mapping = {
        'flow_score': 'flow',
        'divergence_score': 'divergence',
        'reversion_score': 'reversion',
        'inertia_score': 'inertia',
        'value_quality_score': 'value_quality',
    }
    
    for date in df.index:
        exposure_dict = {}
        
        # Map alpha scores to factor exposures
        for col_name, factor_name in factor_mapping.items():
            if col_name in df.columns:
                exposure_dict[factor_name] = float(df.loc[date, col_name])
        
        # Add beta if available (default to 1.0 if not present)
        if 'beta' in df.columns:
            exposure_dict['beta'] = float(df.loc[date, 'beta'])
        else:
            exposure_dict['beta'] = 1.0  # Default market beta
        
        # Add size factor if available
        if 'size' in df.columns:
            exposure_dict['size'] = float(df.loc[date, 'size'])
        
        exposures_list.append(
            FactorExposure(
                symbol=symbol,
                date=pd.Timestamp(date),
                exposures=exposure_dict
            )
        )
    
    return exposures_list


def exposures_to_dataframe(exposures: List[FactorExposure]) -> pd.DataFrame:
    """Convert list of FactorExposure objects to DataFrame
    
    Args:
        exposures: List of FactorExposure objects
    
    Returns:
        DataFrame with MultiIndex (date, symbol) and columns for each factor exposure
    """
    if not exposures:
        return pd.DataFrame()
    
    # Collect all unique factor names
    all_factors = set()
    for exp in exposures:
        all_factors.update(exp.exposures.keys())
    all_factors = sorted(list(all_factors))
    
    # Build data dictionary
    data = []
    for exp in exposures:
        row = {
            'symbol': exp.symbol,
            'date': exp.date,
        }
        for factor in all_factors:
            row[f'exposure_{factor}'] = exp.exposures.get(factor, 0.0)
        data.append(row)
    
    df = pd.DataFrame(data)
    df = df.set_index(['date', 'symbol'])
    
    return df

