"""Tests for Reversion Alpha Factor"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from jgod.alpha_engine.reversion_factor import ReversionFactor


@pytest.fixture
def reversion_factor():
    """Create ReversionFactor instance for testing"""
    return ReversionFactor()


@pytest.fixture
def sample_data():
    """Create sample data for reversion testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Generate price data that moves away from mean (overextension scenario)
    np.random.seed(42)
    mean_price = 100.0
    prices = mean_price + np.cumsum(np.random.randn(100) * 0.5)
    
    df = pd.DataFrame({
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 5000000, 100),
    }, index=dates)
    
    return df


def test_reversion_factor_init(reversion_factor):
    """Test ReversionFactor initialization"""
    assert reversion_factor.name == 'reversion_factor'
    assert reversion_factor.lookback_window == 20
    assert reversion_factor.ma_window == 20


def test_reversion_factor_compute(sample_data, reversion_factor):
    """Test compute method"""
    result = reversion_factor.compute(sample_data)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    assert result.index.equals(sample_data.index)
    
    # Check no NaN values
    assert not result.isna().any()
    
    # Check values are reasonable
    assert result.abs().max() < 10


def test_reversion_factor_empty_data(reversion_factor):
    """Test compute with empty DataFrame"""
    empty_df = pd.DataFrame()
    result = reversion_factor.compute(empty_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_reversion_factor_minimal_data(reversion_factor):
    """Test compute with minimal data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    minimal_df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
    }, index=dates)
    
    result = reversion_factor.compute(minimal_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(minimal_df)
    assert not result.isna().any()


def test_reversion_factor_missing_close(reversion_factor):
    """Test compute without close price"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'volume': np.random.randint(1000000, 5000000, 50),
    }, index=dates)
    
    result = reversion_factor.compute(df)
    
    # Should return zeros when no close price
    assert isinstance(result, pd.Series)
    assert len(result) == len(df)
    assert (result == 0.0).all()

