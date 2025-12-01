"""Tests for Value/Quality Alpha Factor"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from jgod.alpha_engine.value_quality_factor import ValueQualityFactor


@pytest.fixture
def value_quality_factor():
    """Create ValueQualityFactor instance for testing"""
    return ValueQualityFactor()


@pytest.fixture
def sample_data():
    """Create sample data for value/quality testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    df = pd.DataFrame({
        'close': np.random.rand(100) * 100 + 100,
        'roa': np.random.rand(100) * 0.1,  # ROA between 0 and 10%
        'gpa': np.random.rand(100) * 0.2,  # GP/A between 0 and 20%
        'bm': np.random.rand(100) * 2.0,   # B/M between 0 and 2
        'debt_ratio': np.random.rand(100) * 0.5,  # Debt ratio between 0 and 50%
    }, index=dates)
    
    return df


def test_value_quality_factor_init(value_quality_factor):
    """Test ValueQualityFactor initialization"""
    assert value_quality_factor.name == 'value_quality_factor'
    assert value_quality_factor.lookback_window == 252


def test_value_quality_factor_compute(sample_data, value_quality_factor):
    """Test compute method with full fundamental data"""
    result = value_quality_factor.compute(sample_data)
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    assert result.index.equals(sample_data.index)
    
    # Check no NaN values
    assert not result.isna().any()
    
    # Check values are reasonable
    assert result.abs().max() < 10


def test_value_quality_factor_empty_data(value_quality_factor):
    """Test compute with empty DataFrame"""
    empty_df = pd.DataFrame()
    result = value_quality_factor.compute(empty_df)
    
    assert isinstance(result, pd.Series)
    assert len(result) == 0


def test_value_quality_factor_no_fundamental_data(value_quality_factor):
    """Test compute without fundamental data (should return zeros)"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
    }, index=dates)
    
    result = value_quality_factor.compute(df)
    
    # Should return zeros when no fundamental data available
    assert isinstance(result, pd.Series)
    assert len(result) == len(df)
    assert (result == 0.0).all()


def test_value_quality_factor_partial_data(value_quality_factor):
    """Test compute with partial fundamental data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100,
        'roa': np.random.rand(50) * 0.1,
        # Missing other fundamental metrics
    }, index=dates)
    
    result = value_quality_factor.compute(df)
    
    # Should compute using available metrics only
    assert isinstance(result, pd.Series)
    assert len(result) == len(df)
    assert not result.isna().any()

