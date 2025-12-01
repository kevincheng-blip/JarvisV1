"""Tests for Divergence Alpha Factor"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from jgod.alpha_engine.divergence_factor import DivergenceFactor


@pytest.fixture
def divergence_factor():
    """Create DivergenceFactor instance for testing"""
    return DivergenceFactor()


@pytest.fixture
def sample_data():
    """Create sample data for divergence testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Generate price data with trend
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    # Generate volume data (diverging from price)
    volumes = 1000000 + np.random.randint(-200000, 200000, 100)
    
    df = pd.DataFrame({
        'close': prices,
        'volume': volumes,
        'foreign_flow': np.random.randn(100) * 1000000,
        'ecosystem_flow': np.random.randn(100) * 500000,
    }, index=dates)
    
    return df


def test_divergence_factor_init(divergence_factor):
    """Test DivergenceFactor initialization"""
    assert divergence_factor.name == 'divergence_factor'
    assert divergence_factor.lookback_window == 20
    assert divergence_factor.trend_window == 10


def test_divergence_factor_compute(sample_data, divergence_factor):
    """Test compute method"""
    result = divergence_factor.compute(sample_data)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    assert result.index.equals(sample_data.index)
    
    # Check no NaN values
    assert not result.isna().any()
    
    # Check values are reasonable (standardized, should be in reasonable range)
    assert result.abs().max() < 10  # Z-scores typically within [-5, 5]


def test_divergence_factor_empty_data(divergence_factor):
    """Test compute with empty DataFrame"""
    empty_df = pd.DataFrame()
    result = divergence_factor.compute(empty_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_divergence_factor_minimal_data(divergence_factor):
    """Test compute with minimal data (only close and volume)"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    minimal_df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        'volume': np.random.randint(1000000, 5000000, 50),
    }, index=dates)
    
    result = divergence_factor.compute(minimal_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(minimal_df)
    assert not result.isna().any()


def test_divergence_factor_missing_columns(divergence_factor):
    """Test compute with missing optional columns"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        # Missing volume, foreign_flow, etc.
    }, index=dates)
    
    result = divergence_factor.compute(df)
    
    # Should return zeros when no data available
    assert isinstance(result, pd.Series)
    assert len(result) == len(df)
    assert (result == 0.0).all()

