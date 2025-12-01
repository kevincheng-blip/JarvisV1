"""Tests for Inertia Alpha Factor"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from jgod.alpha_engine.inertia_factor import InertiaFactor


@pytest.fixture
def inertia_factor():
    """Create InertiaFactor instance for testing"""
    return InertiaFactor()


@pytest.fixture
def sample_data():
    """Create sample data for inertia testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Generate trending price data
    np.random.seed(42)
    trend = np.linspace(100, 110, 100)
    noise = np.random.randn(100) * 0.5
    prices = trend + noise
    
    df = pd.DataFrame({
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100),
        'buy_volume': np.random.randint(500000, 2500000, 100),
        'sell_volume': np.random.randint(500000, 2500000, 100),
        'foreign_flow': np.random.randn(100) * 1000000,
    }, index=dates)
    
    return df


def test_inertia_factor_init(inertia_factor):
    """Test InertiaFactor initialization"""
    assert inertia_factor.name == 'inertia_factor'
    assert inertia_factor.lookback_window == 20
    assert inertia_factor.momentum_window == 10


def test_inertia_factor_compute(sample_data, inertia_factor):
    """Test compute method"""
    result = inertia_factor.compute(sample_data)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    assert result.index.equals(sample_data.index)
    
    # Check no NaN values
    assert not result.isna().any()
    
    # Check values are reasonable
    assert result.abs().max() < 10


def test_inertia_factor_empty_data(inertia_factor):
    """Test compute with empty DataFrame"""
    empty_df = pd.DataFrame()
    result = inertia_factor.compute(empty_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_inertia_factor_minimal_data(inertia_factor):
    """Test compute with minimal data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    minimal_df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        'volume': np.random.randint(1000000, 5000000, 50),
    }, index=dates)
    
    result = inertia_factor.compute(minimal_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(minimal_df)
    assert not result.isna().any()

